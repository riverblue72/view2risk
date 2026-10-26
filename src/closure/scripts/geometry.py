"""Geometry-only crossing definitions. No signal/trajectory outcome tuning."""
from pathlib import Path
import zipfile
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

MAP = Path('/data/whereami/math/full_rq_261026/assets/imptc_ground_plane.zip')
RGB = np.array([[128,64,128],[244,35,232],[81,0,81],[150,100,100],
                [157,234,50],[229,165,10],[98,160,234],[128,128,128]])

def load_map():
    with zipfile.ZipFile(MAP) as z:
        payload = z.read(next(n for n in z.namelist() if n.endswith('.ply')))
    end = payload.index(b'end_header\n') + len(b'end_header\n')
    header = payload[:end].decode()
    types = {'float':'<f4','double':'<f8','uchar':'u1','char':'i1','int':'<i4','uint':'<u4'}
    fields = []
    for line in header.splitlines():
        if line.startswith('element vertex '):
            count = int(line.split()[-1])
        elif line.startswith('property '):
            _, dtype, name = line.split()
            fields.append((name, types[dtype]))
    a = np.frombuffer(payload, offset=end, count=count, dtype=np.dtype(fields))
    xy = np.column_stack([a['x'],a['y']]).astype(float)
    color = np.column_stack([a[n] for n in ['red','green','blue']])
    labels = np.full(len(a), -1, np.int8)
    for i, rgb in enumerate(RGB):
        labels[(color == rgb).all(axis=1)] = i
    return xy, color, labels

def crosswalks(xy, labels):
    pts = xy[labels == 5]
    origin = pts.min(axis=0)
    cells = np.floor((pts-origin)/.25).astype(int)
    raster = np.zeros(tuple(cells.max(axis=0)+1), bool)
    raster[cells[:,0],cells[:,1]] = True
    closed = ndimage.binary_closing(raster, structure=np.ones((3,3)))
    groups, n = ndimage.label(closed, structure=np.ones((3,3)))
    gids = groups[cells[:,0],cells[:,1]]
    definitions = []
    # Provider diagram labels are assigned by map topology + coordinate origin,
    # not by observed green-entry rates. Centroid correspondence is audited.
    for component in range(1,n+1):
        cloud = pts[gids == component]
        if len(cloud) < 100:
            continue
        center = cloud.mean(axis=0)
        _, axes = np.linalg.eigh(np.cov(cloud.T))
        u = axes[:,-1]
        if u[0] < 0:
            u = -u
        v = np.array([-u[1],u[0]])
        local = (cloud-center) @ np.column_stack([u,v])
        if center[1] < 0:
            signal = 'f1'
        elif center[0] > 15:
            signal = 'f3'
        else:
            signal = 'f2'
        definitions.append(dict(component=component,signal=signal,center=center,
            axis=u,normal=v,cloud=cloud,local=local,
            bounds=np.quantile(local,[.005,.995],axis=0)))
    assert len(definitions) == 3
    assert {d['signal'] for d in definitions} == {'f1','f2','f3'}
    return definitions

def rectangle(d, quantile=.005):
    bounds = np.quantile(d['local'], [quantile,1-quantile], axis=0)
    lo, hi = bounds
    box = np.array([[lo[0],lo[1]],[hi[0],lo[1]],[hi[0],hi[1]],[lo[0],hi[1]],[lo[0],lo[1]]])
    world = box @ np.row_stack([d['axis'],d['normal']]) + d['center']
    return bounds, world

def map_query(xy, labels, positions, workers=2):
    distances, near = cKDTree(xy).query(positions, workers=workers)
    return distances, labels[near]
