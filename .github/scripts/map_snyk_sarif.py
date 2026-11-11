"""Map dependency findings from generated manifests to the tracked source manifests."""

import json
from pathlib import Path
import sys


MANIFESTS = {
    'python': 'setup.py',
    'npm-common': 'package.json',
    'npm-template': 'mtp_common/templates/mtp_common/build_tasks/package.json',
}


def map_sarif(report, target):
    manifest = MANIFESTS[target]
    for run in report['runs']:
        for result in run.get('results', []):
            # Snyk's fixes and line numbers refer to generated, not tracked, manifests.
            result.pop('fixes', None)
            locations = result.setdefault('locations', [{}])
            if not locations:
                locations.append({})
            for location in locations:
                physical = location.setdefault('physicalLocation', {})
                physical['artifactLocation'] = {'uri': manifest}
                physical['region'] = {'startLine': 1}
    return report


def main():
    report_path = Path(sys.argv[1])
    report = json.loads(report_path.read_text())
    map_sarif(report, sys.argv[2])
    report_path.write_text(json.dumps(report))


if __name__ == '__main__':
    main()
