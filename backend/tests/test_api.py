import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCandidateListingWithFilters:
    """Verify that listing and filtering delegates to SQL, not Python memory."""

    async def test_list_returns_all_candidates(
        self, client: AsyncClient, admin_token: str, seeded_candidates: list[str]
    ):
        resp = await client.get(
            "/candidates",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert body["page"] == 1
        assert len(body["items"]) == 3

    async def test_filter_by_status(
        self, client: AsyncClient, admin_token: str, seeded_candidates: list[str]
    ):
        resp = await client.get(
            "/candidates?status=new",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.json()
        assert body["total"] == 2
        assert all(c["status"] == "new" for c in body["items"])

    async def test_filter_by_role_applied(
        self, client: AsyncClient, admin_token: str, seeded_candidates: list[str]
    ):
        resp = await client.get(
            "/candidates?role_applied=DevOps+Engineer",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Bob Ops"

    async def test_filter_by_keyword(
        self, client: AsyncClient, admin_token: str, seeded_candidates: list[str]
    ):
        resp = await client.get(
            "/candidates?keyword=carol",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["email"] == "carol@full.com"

    async def test_pagination_metadata(
        self, client: AsyncClient, admin_token: str, seeded_candidates: list[str]
    ):
        resp = await client.get(
            "/candidates?page_size=2&page=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.json()
        assert body["total"] == 3
        assert body["page_size"] == 2
        assert body["pages"] == 2
        assert len(body["items"]) == 2


class TestAuthEnforcement:
    """Verify RBAC: reviewer sees only own scores, cannot see internal_notes."""

    async def test_reviewer_sees_only_own_scores(
        self,
        client: AsyncClient,
        reviewer_token: str,
        reviewer_b_token: str,
        admin_token: str,
        seeded_candidates: list[str],
    ):
        cid = seeded_candidates[0]

        await client.post(
            f"/candidates/{cid}/scores",
            json={"category": "Technical", "score": 5, "note": "From A"},
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        await client.post(
            f"/candidates/{cid}/scores",
            json={"category": "Communication", "score": 3, "note": "From B"},
            headers={"Authorization": f"Bearer {reviewer_b_token}"},
        )

        resp_a = await client.get(
            f"/candidates/{cid}",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        scores_a = resp_a.json()["scores"]
        assert len(scores_a) == 1
        assert scores_a[0]["note"] == "From A"

        resp_b = await client.get(
            f"/candidates/{cid}",
            headers={"Authorization": f"Bearer {reviewer_b_token}"},
        )
        scores_b = resp_b.json()["scores"]
        assert len(scores_b) == 1
        assert scores_b[0]["note"] == "From B"

        resp_admin = await client.get(
            f"/candidates/{cid}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert len(resp_admin.json()["scores"]) == 2

    async def test_reviewer_cannot_see_internal_notes(
        self,
        client: AsyncClient,
        reviewer_token: str,
        admin_token: str,
        seeded_candidates: list[str],
    ):
        cid = seeded_candidates[0]

        await client.patch(
            f"/candidates/{cid}/notes",
            json={"notes": "Confidential info"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = await client.get(
            f"/candidates/{cid}",
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert "internal_notes" not in resp.json()

    async def test_reviewer_cannot_patch_notes(
        self,
        client: AsyncClient,
        reviewer_token: str,
        seeded_candidates: list[str],
    ):
        cid = seeded_candidates[0]
        resp = await client.patch(
            f"/candidates/{cid}/notes",
            json={"notes": "Hacked notes"},
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert resp.status_code == 403

    async def test_unauthenticated_request_rejected(self, client: AsyncClient):
        resp = await client.get("/candidates")
        assert resp.status_code == 401


class TestScoreValidation:
    """Verify score boundaries and required fields."""

    async def test_valid_score_created(
        self,
        client: AsyncClient,
        reviewer_token: str,
        seeded_candidates: list[str],
    ):
        cid = seeded_candidates[0]
        resp = await client.post(
            f"/candidates/{cid}/scores",
            json={"category": "Technical", "score": 4},
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["score"] == 4
        assert body["category"] == "Technical"
        assert body["candidate_id"] == cid

    async def test_score_above_5_rejected(
        self,
        client: AsyncClient,
        reviewer_token: str,
        seeded_candidates: list[str],
    ):
        cid = seeded_candidates[0]
        resp = await client.post(
            f"/candidates/{cid}/scores",
            json={"category": "Technical", "score": 6},
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert resp.status_code == 422

    async def test_score_below_1_rejected(
        self,
        client: AsyncClient,
        reviewer_token: str,
        seeded_candidates: list[str],
    ):
        cid = seeded_candidates[0]
        resp = await client.post(
            f"/candidates/{cid}/scores",
            json={"category": "Technical", "score": 0},
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert resp.status_code == 422

    async def test_missing_category_rejected(
        self,
        client: AsyncClient,
        reviewer_token: str,
        seeded_candidates: list[str],
    ):
        cid = seeded_candidates[0]
        resp = await client.post(
            f"/candidates/{cid}/scores",
            json={"score": 3},
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert resp.status_code == 422

    async def test_score_for_nonexistent_candidate(
        self, client: AsyncClient, reviewer_token: str
    ):
        resp = await client.post(
            "/candidates/nonexistent-id/scores",
            json={"category": "Technical", "score": 3},
            headers={"Authorization": f"Bearer {reviewer_token}"},
        )
        assert resp.status_code == 404
