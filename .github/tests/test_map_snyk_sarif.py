import importlib.util
from pathlib import Path
import unittest


script = Path(__file__).parents[1] / 'scripts' / 'map_snyk_sarif.py'
spec = importlib.util.spec_from_file_location('map_snyk_sarif', script)
mapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mapper)


class MapSnykSarifTests(unittest.TestCase):
    def test_findings_link_to_tracked_manifests_without_generated_fixes(self):
        for target, expected in mapper.MANIFESTS.items():
            with self.subTest(target=target):
                report = {'runs': [{'results': [{
                    'ruleId': 'SNYK-EXAMPLE',
                    'message': {'text': 'Dependency issue'},
                    'fixes': [{'description': {'text': 'Change generated file'}}],
                    'locations': [{'physicalLocation': {
                        'artifactLocation': {'uri': '/tmp/generated/package.json', 'index': 0},
                        'region': {'startLine': 99},
                    }}],
                }]}]}
                result = mapper.map_sarif(report, target)['runs'][0]['results'][0]
                self.assertEqual(result['ruleId'], 'SNYK-EXAMPLE')
                self.assertEqual(result['message']['text'], 'Dependency issue')
                self.assertNotIn('fixes', result)
                physical = result['locations'][0]['physicalLocation']
                self.assertEqual(physical['artifactLocation'], {'uri': expected})
                self.assertEqual(physical['region'], {'startLine': 1})

    def test_no_findings_remains_a_valid_empty_report(self):
        report = {'runs': [{'results': []}]}
        self.assertEqual(mapper.map_sarif(report, 'python'), report)

    def test_unknown_target_is_rejected(self):
        with self.assertRaises(KeyError):
            mapper.map_sarif({'runs': []}, 'unknown')


if __name__ == '__main__':
    unittest.main()
