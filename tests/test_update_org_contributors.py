import unittest

from scripts.update_org_contributors import render_contributors


class RenderContributorsTests(unittest.TestCase):
    def test_renders_unique_contributors_sorted_by_contributions(self):
        contributors = [
            {
                "login": "alice",
                "html_url": "https://github.com/alice",
                "avatar_url": "https://github.com/alice.png",
                "contributions": 3,
            },
            {
                "login": "bob",
                "html_url": "https://github.com/bob",
                "avatar_url": "https://github.com/bob.png",
                "contributions": 7,
            },
        ]

        rendered = render_contributors(contributors)

        self.assertLess(rendered.index("@bob"), rendered.index("@alice"))
        self.assertEqual(rendered.count('href="https://github.com/alice"'), 1)
        self.assertIn("<!-- ORGANIZATION-CONTRIBUTORS:START -->", rendered)
        self.assertIn("<!-- ORGANIZATION-CONTRIBUTORS:END -->", rendered)


if __name__ == "__main__":
    unittest.main()
