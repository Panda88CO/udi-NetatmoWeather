"""Unit tests for Universal Devices profile XML and NLS files."""
import os
import re
import unittest
import xml.etree.ElementTree as ET

PROFILE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'profile'))
EDITORS_PATH = os.path.join(PROFILE_DIR, 'editor', 'editors.xml')
NODEDEF_PATH = os.path.join(PROFILE_DIR, 'nodedef', 'nodedef.xml')
NLS_PATH = os.path.join(PROFILE_DIR, 'nls', 'en_us.txt')


class TestProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.editors_tree = ET.parse(EDITORS_PATH)
        cls.nodedef_tree = ET.parse(NODEDEF_PATH)
        with open(NLS_PATH, 'r', encoding='utf-8') as f:
            cls.nls_content = f.read()

        cls.editor_ids = {e.attrib['id'] for e in cls.editors_tree.getroot().findall('editor')}
        cls.nodedef_nodes = cls.nodedef_tree.getroot().findall('nodeDef')
        cls.nodedef_ids = {nd.attrib['id'] for nd in cls.nodedef_nodes}

    def test_xml_files_exist(self):
        """Verify all profile files exist."""
        self.assertTrue(os.path.exists(EDITORS_PATH), f"Missing {EDITORS_PATH}")
        self.assertTrue(os.path.exists(NODEDEF_PATH), f"Missing {NODEDEF_PATH}")
        self.assertTrue(os.path.exists(NLS_PATH), f"Missing {NLS_PATH}")

    def test_editor_ids_uppercase_alphanumeric_without_special_chars(self):
        """Verify editor IDs are uppercase alphanumeric and contain no special characters like _."""
        for eid in self.editor_ids:
            with self.subTest(editor_id=eid):
                self.assertRegex(
                    eid,
                    r'^[A-Z0-9]+$',
                    f"Editor ID '{eid}' must only contain uppercase alphanumeric characters without special characters."
                )

    def test_nodedef_ids_uppercase_alphanumeric_without_special_chars(self):
        """Verify nodeDef IDs are uppercase alphanumeric and contain no special characters like _."""
        for ndid in self.nodedef_ids:
            with self.subTest(nodedef_id=ndid):
                self.assertRegex(
                    ndid,
                    r'^[A-Z0-9]+$',
                    f"NodeDef ID '{ndid}' must only contain uppercase alphanumeric characters without special characters."
                )

    def test_no_reserved_words_in_editor_ids(self):
        """Verify known Universal Devices reserved keywords like 'STATUS' are not used as editor IDs."""
        reserved_keywords = {'STATUS'}
        conflicts = self.editor_ids.intersection(reserved_keywords)
        self.assertEqual(
            conflicts,
            set(),
            f"Editor IDs contain reserved words: {conflicts}"
        )

    def test_all_nodedef_referenced_editors_are_defined(self):
        """Verify every editor attribute in nodedef.xml maps to an existing editor in editors.xml."""
        used_editors = set()
        for st in self.nodedef_tree.getroot().findall('.//st'):
            if 'editor' in st.attrib:
                used_editors.add(st.attrib['editor'])

        missing = used_editors - self.editor_ids
        self.assertEqual(
            missing,
            set(),
            f"The following editors are referenced in nodedef.xml but not defined in editors.xml: {missing}"
        )

    def test_range_elements_have_valid_uom(self):
        """Verify every <range> element in editors.xml has a valid integer UOM attribute."""
        for editor in self.editors_tree.getroot().findall('editor'):
            ranges = editor.findall('range')
            self.assertGreater(
                len(ranges),
                0,
                f"Editor '{editor.attrib.get('id')}' must define at least one <range> element."
            )
            for r in ranges:
                self.assertIn('uom', r.attrib, f"Range in editor '{editor.attrib.get('id')}' missing 'uom'")
                uom_val = r.attrib['uom']
                self.assertTrue(uom_val.isdigit(), f"Range uom '{uom_val}' is not a numeric integer")

    def test_nls_contains_all_nodedef_names_and_icons(self):
        """Verify profile/nls/en_us.txt defines ND-<ID>-NAME and ND-<ID>-ICON for each nodeDef."""
        for ndid in self.nodedef_ids:
            with self.subTest(nodedef_id=ndid):
                name_key = f"ND-{ndid}-NAME"
                icon_key = f"ND-{ndid}-ICON"
                self.assertIn(name_key, self.nls_content, f"Missing {name_key} in en_us.txt")
                self.assertIn(icon_key, self.nls_content, f"Missing {icon_key} in en_us.txt")

    def test_nls_trend_mapping(self):
        """Verify TREND editor NLS keys exist in en_us.txt without underscores."""
        trend_editor = None
        for ed in self.editors_tree.getroot().findall('editor'):
            if ed.attrib.get('id') == 'TREND':
                trend_editor = ed
                break

        self.assertIsNotNone(trend_editor, "TREND editor not found in editors.xml")
        r = trend_editor.find('range')
        self.assertIsNotNone(r, "TREND editor missing <range>")
        nls_ref = r.attrib.get('nls')
        self.assertRegex(nls_ref, r'^[A-Z0-9]+$', f"NLS reference '{nls_ref}' must be uppercase alphanumeric without _")
        self.assertIn(f"{nls_ref}-0", self.nls_content)
        self.assertIn(f"{nls_ref}-1", self.nls_content)
        self.assertIn(f"{nls_ref}-2", self.nls_content)

    def test_status_driver_ids_valid(self):
        """Verify all <st id="..."> drivers in nodedef.xml are valid ISY driver names (ST, GV0-GV30)."""
        valid_gv_pattern = re.compile(r'^(ST|GV([0-9]|[12][0-9]|30))$')
        for nd in self.nodedef_nodes:
            ndid = nd.attrib['id']
            for st in nd.findall('.//st'):
                stid = st.attrib['id']
                with self.subTest(node=ndid, driver=stid):
                    self.assertTrue(
                        valid_gv_pattern.match(stid),
                        f"Driver id '{stid}' in node '{ndid}' is not a recognized ISY status driver."
                    )

    def test_version_consistency(self):
        """Verify version consistency between server.json and profile/version.txt."""
        server_json_path = os.path.join(PROFILE_DIR, '..', 'server.json')
        version_txt_path = os.path.join(PROFILE_DIR, 'version.txt')
        self.assertTrue(os.path.exists(server_json_path))
        self.assertTrue(os.path.exists(version_txt_path))

        import json
        with open(server_json_path, 'r', encoding='utf-8') as f:
            server_data = json.load(f)
        with open(version_txt_path, 'r', encoding='utf-8') as f:
            version_txt = f.read().strip()

        profile_version = server_data.get('profile_version')
        package_version = server_data['credits'][0]['version']

        import mainNetatmo
        self.assertEqual(profile_version, version_txt)
        self.assertEqual(package_version, version_txt)
        self.assertEqual(mainNetatmo.__version__, version_txt)
        self.assertRegex(version_txt, r'^\d+\.\d+\.\d+$')


if __name__ == '__main__':
    unittest.main()

