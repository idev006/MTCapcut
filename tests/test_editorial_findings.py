import unittest

from mtcapcut.editorial_findings import (
    EditorialFinding, FindingCategory, FindingSeverity, ReleaseScope, compute_release_gates,
)


def finding(severity, scopes=()):
    return EditorialFinding("f1", "fact_ethics_critic", FindingCategory.FACT, severity,
                            "finding", ("o1",), "resolve", "fact_editor", tuple(scopes))


class EditorialFindingTests(unittest.TestCase):
    def test_warning_does_not_block_private_preview(self):
        gates = compute_release_gates((finding(FindingSeverity.MEDIUM),), (), "private_preview")
        self.assertTrue(gates.private_preview_eligible)
        self.assertFalse(gates.publication_eligible)

    def test_private_blocker_blocks_both_scopes(self):
        gates = compute_release_gates((finding(FindingSeverity.CRITICAL,
            (ReleaseScope.PRIVATE_PREVIEW, ReleaseScope.PUBLICATION)),), (), "publication")
        self.assertFalse(gates.private_preview_eligible)
        self.assertFalse(gates.publication_eligible)

    def test_publication_blocker_allows_private_preview(self):
        gates = compute_release_gates((finding(FindingSeverity.HIGH, (ReleaseScope.PUBLICATION,)),),
                                      (), "publication")
        self.assertTrue(gates.private_preview_eligible)
        self.assertFalse(gates.publication_eligible)

    def test_rights_blocker_only_blocks_publication(self):
        gates = compute_release_gates((), ("asset-1",), "publication")
        self.assertTrue(gates.private_preview_eligible)
        self.assertFalse(gates.publication_eligible)


if __name__ == "__main__":
    unittest.main()
