"""Draw the portfolio figure from saved KITTI 00 trajectories (no model rerun).

Usage: python scripts/draw_looplens.py --project-root /path/to/vpr-loop-closure
       --ground-truth /path/to/KITTI/dataset/poses/00.txt

Each trajectory is independently rigidly aligned to ground truth, without scale
correction. Every frame is used for metrics and curves. The output is an inline
SVG Jinja include so the website can apply its light/dark colors. A standalone
SVG with the same data and light-theme colors is also exported.

The inline copy is compacted (metadata removed, polylines simplified to within
COMPACT_TOLERANCE px, coordinates rounded) because it ships with every page.
Run with --compact-only to re-compact the existing include without the data.
"""
import argparse
import io
from pathlib import Path
import re

COMPACT_TOLERANCE = 0.2  # SVG user units; far below one rendered pixel.


def _simplify(points, tolerance):
    """Ramer–Douglas–Peucker polyline simplification (iterative, pure Python)."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        (x1, y1), (x2, y2) = points[start], points[end]
        dx, dy = x2 - x1, y2 - y1
        length = (dx * dx + dy * dy) ** .5
        worst, index = 0.0, None
        for i in range(start + 1, end):
            x, y = points[i]
            distance = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / length if length else ((x - x1) ** 2 + (y - y1) ** 2) ** .5
            if distance > worst:
                worst, index = distance, i
        if index is not None and worst > tolerance:
            keep[index] = True
            stack += [(start, index), (index, end)]
    return [point for point, kept in zip(points, keep) if kept]


def _number(value):
    text = f'{value:.1f}'.rstrip('0').rstrip('.')
    return '0' if text == '-0' else text


def compact_svg(svg, tolerance=COMPACT_TOLERANCE):
    """Shrink a Matplotlib SVG for inlining without visibly changing it."""
    svg = re.sub(r'\s*<metadata>.*?</metadata>', '', svg, flags=re.S)
    svg = re.sub(r'\s*<title>LoopLens: KITTI 00 trajectory correction</title>', '', svg)

    def path(match):
        commands = re.findall(r'([MLz])\s*([-\d.e]+)?\s*([-\d.e]+)?', match.group(1))
        if any(command not in 'ML' for command, *_ in commands) or [c for c, *_ in commands].count('M') != 1:
            parts = [command if command == 'z' else f'{command}{_number(float(x))} {_number(float(y))}' for command, x, y in commands]
            return f'd="{"".join(parts)}"'
        points = _simplify([(float(x), float(y)) for _, x, y in commands], tolerance)
        return 'd="M' + 'L'.join(f'{_number(x)} {_number(y)}' for x, y in points) + '"'

    svg = re.sub(r'd="(M[^"]*)"', path, svg)
    svg = re.sub(r'(\s(?:x|y|width|height)=")(-?\d+\.\d+)"', lambda m: f'{m.group(1)}{_number(float(m.group(2)))}"', svg)
    svg = re.sub(r'(rotate\(-?0 )([\d.]+) ([\d.]+)\)', lambda m: f'{m.group(1)}{_number(float(m.group(2)))} {_number(float(m.group(3)))})', svg)
    return "\n".join(line.strip() for line in svg.splitlines() if line.strip()) + "\n"


def positions(path):
    return np.loadtxt(path).reshape(-1, 3, 4)[:, :, 3]


def align(xyz, ground_truth):
    a = xyz - xyz.mean(0)
    b = ground_truth - ground_truth.mean(0)
    u, _, vt = np.linalg.svd(a.T @ b)
    sign = np.eye(3)
    sign[-1, -1] = np.linalg.det(u @ vt)
    return a @ (u @ sign @ vt) + ground_truth.mean(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path)
    parser.add_argument('--ground-truth', type=Path)
    parser.add_argument('--compact-only', action='store_true', help='re-compact templates/illustrations/looplens.svg in place')
    args = parser.parse_args()
    site = Path(__file__).resolve().parents[1]
    include = site / 'templates/illustrations/looplens.svg'
    if args.compact_only:
        before_size = include.stat().st_size
        include.write_text(compact_svg(include.read_text()))
        print(f'{include.name}: {before_size} → {include.stat().st_size} bytes')
        return
    if not (args.project_root and args.ground_truth):
        parser.error('--project-root and --ground-truth are required unless --compact-only is used')
    global np  # positions() and align() use NumPy; only plotting needs it installed.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    truth = positions(args.ground_truth)
    before = positions(args.project_root / 'slam/runs/kitti_off/CameraTrajectory.txt')
    after = positions(args.project_root / 'slam/runs/vpr_kitti.txt')
    if truth.shape != before.shape or truth.shape != after.shape:
        raise ValueError('All trajectories must contain the same frames.')
    before, after = align(before, truth), align(after, truth)
    errors_before = np.linalg.norm(before - truth, axis=1)
    errors_after = np.linalg.norm(after - truth, axis=1)
    rmse_before, rmse_after = np.sqrt(np.mean(errors_before**2)), np.sqrt(np.mean(errors_after**2))
    print(f'{len(truth)} frames; ATE RMSE: {rmse_before:.3f} m → {rmse_after:.3f} m')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'svg.fonttype': 'none', 'svg.hashsalt': 'looplens-kitti00', 'axes.labelcolor': '#626e67', 'xtick.color': '#626e67', 'ytick.color': '#626e67', 'text.color': '#626e67'})
    fig = plt.figure(figsize=(6.2, 5.6))
    grid = fig.add_gridspec(2, 1, height_ratios=[3.1, 1], hspace=.52, top=.98, bottom=.12, left=.13, right=.97)
    route = fig.add_subplot(grid[0])
    error = fig.add_subplot(grid[1])
    colors = {'truth': '#8c9690', 'before': '#af7048', 'after': '#2d6556'}
    route.plot(truth[:, 0], truth[:, 2], color=colors['truth'], lw=3, alpha=.6)
    route.plot(before[:, 0], before[:, 2], color=colors['before'], lw=1.35)
    route.plot(after[:, 0], after[:, 2], color=colors['after'], lw=1.35)
    route.set_aspect('equal')
    route.set(xlim=(-335, 340), ylim=(-45, 510), xlabel='x (m)', ylabel='z (m)')
    route.set_xticks([-300, 0, 300])
    route.set_yticks([0, 250, 500])
    error.plot(errors_before, color=colors['before'], lw=1.25)
    error.plot(errors_after, color=colors['after'], lw=1.25)
    error.set(xlim=(0, len(truth)-1), ylim=(0, 10), xlabel='Frame', ylabel='Error (m)')
    error.set_xticks([0, 2000, 4000])
    error.set_yticks([0, 5, 10])
    for axis in (route, error):
        axis.grid(color='#dce1d9', linewidth=.65)
        axis.set_axisbelow(True)
        axis.tick_params(length=0, labelsize=10, pad=5)
        for spine in axis.spines.values():
            spine.set_visible(False)
    output = io.StringIO()
    fig.savefig(output, format='svg', transparent=True, metadata={'Date': None, 'Title': 'LoopLens: KITTI 00 trajectory correction', 'Description': 'Saved ORB-SLAM3 stereo trajectories before and after custom loop closure. Rigid alignment without scale correction; translation error uses all 4541 frames.'})
    plt.close(fig)
    svg = "\n".join(line.rstrip() for line in output.getvalue().splitlines()) + "\n"
    (site / 'static/images/projects/looplens-kitti00.svg').write_text(svg)
    svg = svg[svg.index('<svg'):]
    svg = re.sub(r'width="[^"]+" height="[^"]+"', '', svg, count=1)
    svg = svg.replace('<svg ', '<svg class="project-diagram trajectory-diagram" role="img" aria-labelledby="looplens-plot-title looplens-plot-desc" ', 1)
    end = svg.index('>') + 1
    svg = svg[:end] + '<title id="looplens-plot-title">KITTI 00 trajectory and translation error</title><desc id="looplens-plot-desc">Ground truth is grey, the trajectory before loop closure is orange, and the optimized trajectory is green. The lower plot shows per-frame translation error after rigid alignment, without rescaling. ATE RMSE decreases from 4.335 to 1.956 metres over 4541 frames.</desc>' + svg[end:]
    svg = svg.replace('*{stroke-linejoin:', '.trajectory-diagram *{stroke-linejoin:')
    for color, variable in {'#626e67': '--muted', '#dce1d9': '--border', '#8c9690': '--diagram-reference', '#af7048': '--diagram-warm', '#2d6556': '--accent'}.items():
        svg = svg.replace(color, f'var({variable})')
    include.write_text(compact_svg(svg))


if __name__ == '__main__':
    main()
