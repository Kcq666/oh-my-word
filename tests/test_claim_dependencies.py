import unittest

from oh_my_patent.lint import check_claims
from oh_my_patent.schema import PatentDraft, build_claim, parse_claims_block
from oh_my_patent.spec import Font, RenderOptions
from oh_my_patent.render import DocxRenderer


class ClaimDependenciesTest(unittest.TestCase):
    def codes(self, text):
        draft = PatentDraft(title='一种装置')
        draft.claims = parse_claims_block(text)
        return {issue.code for issue in check_claims(draft)}

    def test_first_dependent_is_not_repaired(self):
        claim = build_claim(1, '根据权利要求2所述的装置，其特征在于，含壳体。')
        self.assertFalse(claim.independent)
        self.assertEqual(claim.references, [2])
        self.assertIn('CLAIM-010', self.codes(claim.render_text()))

    def test_missing_reference_number(self):
        self.assertIn('CLAIM-006', self.codes('1. 根据权利要求所述的装置，其特征在于，含壳体。'))

    def test_conjunctive_and_ambiguous_references(self):
        prefix = '1. 一种装置，其特征在于，含壳体。\n2. 根据权利要求1所述的装置，其特征在于，含盖体。\n'
        for ref in ['1和2', '1及2', '1以及2', '1、2', '1-2', '1和2中任一项']:
            with self.subTest(ref=ref):
                self.assertIn('CLAIM-014', self.codes(prefix + f'3. 根据权利要求{ref}所述的装置，其特征在于，含弹簧或垫片。'))

    def test_alternative_references(self):
        prefix = '1. 一种装置，其特征在于，含壳体。\n2. 根据权利要求1所述的装置，其特征在于，含盖体。\n'
        for ref in ['1或2', '1或者2', '1或权利要求2', '1至2中任一项', '1、2中的任一项']:
            with self.subTest(ref=ref):
                self.assertNotIn('CLAIM-014', self.codes(prefix + f'3. 根据权利要求{ref}所述的装置，其特征在于，含弹簧。'))

    def test_multiple_on_multiple_rejected_but_single_allowed(self):
        prefix = ('1. 一种装置，其特征在于，含壳体。\n'
                  '2. 根据权利要求1所述的装置，其特征在于，含盖体。\n'
                  '3. 根据权利要求1或2所述的装置，其特征在于，含弹簧。\n')
        self.assertIn('CLAIM-015', self.codes(prefix + '4. 根据权利要求1或3所述的装置，其特征在于，含垫片。'))
        self.assertNotIn('CLAIM-015', self.codes(prefix + '4. 根据权利要求3所述的装置，其特征在于，含垫片。'))

    def test_reference_to_absent_claim(self):
        self.assertIn('CLAIM-016', self.codes('1. 一种装置，其特征在于，含壳体。\n3. 根据权利要求2所述的装置，其特征在于，含盖体。'))

    def test_render_options_boundaries_and_direct_api(self):
        for size in [10, 12, 14]:
            RenderOptions(body_size=size, line_spacing=1).validate()
        for size, spacing in [(6, 1.5), (8, 1.5), (12, 0.2), (float('nan'), 1.5), (12, float('inf'))]:
            for method in ['render', 'render_split']:
                with self.subTest(size=size, spacing=spacing, method=method):
                    with self.assertRaises(ValueError):
                        getattr(DocxRenderer(PatentDraft(title='一种装置'), RenderOptions(body_size=size, line_spacing=spacing)), method)()

    def test_unsupported_body_font_rejected(self):
        with self.assertRaises(ValueError):
            DocxRenderer(PatentDraft(title='一种装置'), RenderOptions(font=Font.HEI)).render()
