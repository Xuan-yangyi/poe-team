"""
Integration tests with real PostgreSQL database.
Tests end-to-end API workflows with actual DB operations.
"""
import pytest
import uuid


# These UUIDs match the seeded test_materials and test_lots fixtures
MAT_A = "00000000-0000-0000-0000-000000000001"
MAT_B = "00000000-0000-0000-0000-000000000002"
MAT_C = "00000000-0000-0000-0000-000000000003"
LOT_A = "00000000-0000-0000-0000-000000000001"
LOT_B = "00000000-0000-0000-0000-000000000002"
NOT_FOUND_UUID = "00000000-0000-0000-0000-00000000ffff"


@pytest.mark.usefixtures("test_materials", "test_lots")
class TestWorkOrderFlow:
    async def test_create_and_issue(self, client, auth_headers):
        resp = await client.post("/work-orders", json={
            "idh_id": "IDH-TEST",
            "customer_id": "CUST-A",
            "due_date": "2026-12-01",
            "bom_ver": "v1.0",
            "settle_mode": "purchase",
            "priority": 5,
            "lines": [
                {"material_id": MAT_A, "qty_ordered": 1000, "unit_price": "1.50"},
                {"material_id": MAT_B, "qty_ordered": 500, "unit_price": "2.00"},
            ]
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        wo_id = data["data"]["id"]
        wo_no = data["data"]["wo_no"]
        assert wo_no.startswith("WO-")

        # Fetch it
        resp = await client.get(f"/work-orders/{wo_id}", headers=auth_headers)
        assert resp.status_code == 200
        wo = resp.json()["data"]
        assert wo["status"] == "draft"
        assert len(wo["lines"]) == 2

        # Issue
        resp = await client.post(f"/work-orders/{wo_id}/issue", headers=auth_headers)
        assert resp.status_code == 200

        # Verify issued
        resp = await client.get(f"/work-orders/{wo_id}", headers=auth_headers)
        assert resp.json()["data"]["status"] == "issued"

    async def test_list_with_filters(self, client, auth_headers):
        resp = await client.get("/work-orders?status=draft&page=1&page_size=5", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data
        assert "meta" in data


@pytest.mark.usefixtures("test_materials", "test_lots")
class TestShipmentFlow:
    async def test_create_shipment(self, client, auth_headers):
        # Create work order
        resp = await client.post("/work-orders", json={
            "idh_id": "IDH-SHIP",
            "due_date": "2026-12-01",
            "lines": [{"material_id": MAT_A, "qty_ordered": 100}]
        }, headers=auth_headers)
        wo_id = resp.json()["data"]["id"]

        # Issue
        await client.post(f"/work-orders/{wo_id}/issue", headers=auth_headers)

        # Create shipment
        resp = await client.post("/shipments", json={
            "wo_id": wo_id,
            "idh_id": "IDH-SHIP",
            "eta": "2026-12-01",
            "lines": [{
                "material_id": MAT_A,
                "lot_id": LOT_A,
                "container_id": "BOX-001",
                "qty_per_container": 100,
                "qty_shipped": 100
            }]
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "dn_no" in data["data"]

        ship_id = data["data"]["id"]

        # Confirm
        resp = await client.post(f"/shipments/{ship_id}/confirm", headers=auth_headers)
        assert resp.status_code == 200

        # Goods receipt
        resp = await client.post("/goods-receipts", json={
            "dn_no": data["data"]["dn_no"],
            "container_id": "BOX-001",
            "lot_id": LOT_A,
            "qty_received": 100,
            "qty_shipped": 100,
            "diff_reason": "",
            "received_by": "TEST_USER"
        }, headers=auth_headers)
        assert resp.status_code == 200


class TestInventoryQuery:
    async def test_stock_empty(self, client, auth_headers):
        resp = await client.get("/inventory/stock", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "meta" in data

    async def test_stock_with_filters(self, client, auth_headers):
        resp = await client.get(
            "/inventory/stock?status=available&owner=factory&page=1&page_size=10",
            headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0


@pytest.mark.usefixtures("test_materials", "test_lots")
class TestProduction:
    async def test_create_issue(self, client, auth_headers):
        # Create work order first
        wo_resp = await client.post("/work-orders", json={
            "idh_id": "IDH-PROD",
            "due_date": "2026-12-01",
            "lines": [{"material_id": MAT_C, "qty_ordered": 500}]
        }, headers=auth_headers)
        wo_id = wo_resp.json()["data"]["id"]

        resp = await client.post("/issues", json={
            "wo_id": wo_id,
            "lot_id": LOT_B,
            "material_id": MAT_C,
            "qty": 100,
            "operator": "OP001",
            "scan_method": "h5"
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["qty"] == 100

    async def test_wip_report_valid(self, client, auth_headers):
        wo_resp = await client.post("/work-orders", json={
            "idh_id": "IDH-WIP",
            "due_date": "2026-12-01",
            "lines": [{"material_id": MAT_C, "qty_ordered": 200}]
        }, headers=auth_headers)
        wo_id = wo_resp.json()["data"]["id"]

        resp = await client.post("/wip-reports", json={
            "wo_id": wo_id,
            "process_code": "SMT",
            "process_seq": 1,
            "qty_in": 100,
            "qty_out": 95,
            "qty_scrap": 2
        }, headers=auth_headers)
        assert resp.status_code == 200

    async def test_wip_report_scrap_overflow(self, client, auth_headers):
        wo_resp = await client.post("/work-orders", json={
            "idh_id": "IDH-SCRAP",
            "due_date": "2026-12-01",
            "lines": [{"material_id": MAT_C, "qty_ordered": 300}]
        }, headers=auth_headers)
        wo_id = wo_resp.json()["data"]["id"]

        resp = await client.post("/wip-reports", json={
            "wo_id": wo_id,
            "process_code": "SMT",
            "process_seq": 1,
            "qty_in": 100,
            "qty_out": 50,
            "qty_scrap": 60
        }, headers=auth_headers)
        assert resp.status_code == 422
        assert "产出+报废不能超过投入" in resp.json()["detail"]["message"]

    async def test_fg_receipt(self, client, auth_headers):
        wo_resp = await client.post("/work-orders", json={
            "idh_id": "IDH-FG",
            "due_date": "2026-12-01",
            "lines": [{"material_id": MAT_C, "qty_ordered": 10}]
        }, headers=auth_headers)
        wo_id = wo_resp.json()["data"]["id"]

        sn = f"SN-{uuid.uuid4().hex[:8]}"
        resp = await client.post("/fg-receipts", json={
            "wo_id": wo_id,
            "sn": sn,
            "qty": 1,
            "lot_id": LOT_B,
            "received_by": "RCV001"
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["sn"] == sn

        # Duplicate SN should fail
        resp2 = await client.post("/fg-receipts", json={
            "wo_id": wo_id,
            "sn": sn,
            "qty": 1,
            "lot_id": LOT_B,
            "received_by": "RCV001"
        }, headers=auth_headers)
        assert resp2.status_code == 409


class TestReconciliation:
    async def test_create_period(self, client, auth_headers):
        unique_period = f"2026-{10 + uuid.uuid4().int % 2:02d}"
        resp = await client.post("/reconciliation/periods", json={
            "period": unique_period,
            "idh_id": f"IDH-{uuid.uuid4().hex[:4]}"
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["period"] == unique_period

        period_id = data["data"]["id"]

        # Fetch
        resp = await client.get(f"/reconciliation/periods/{period_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Get items (empty)
        resp = await client.get(f"/reconciliation/periods/{period_id}/items", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    async def test_invalid_period_format(self, client, auth_headers):
        resp = await client.post("/reconciliation/periods", json={
            "period": "2026", "idh_id": "IDH-01"
        }, headers=auth_headers)
        assert resp.status_code == 422

    async def test_period_not_found(self, client, auth_headers):
        resp = await client.get("/reconciliation/periods/9999999", headers=auth_headers)
        assert resp.status_code == 404


class TestAlerts:
    async def test_list_alerts(self, client, auth_headers):
        resp = await client.get("/alerts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    async def test_alert_not_found(self, client, auth_headers):
        resp = await client.post(f"/alerts/{NOT_FOUND_UUID}/acknowledge",
                                 json={"acknowledged_by": "admin"}, headers=auth_headers)
        assert resp.status_code == 404


class TestConversations:
    async def test_create_and_message(self, client, auth_headers):
        # Create conversation
        resp = await client.post("/conversations", json={
            "conv_type": "wo",
            "ref_id": "wo-test-flow",
            "title": "Integration test conversation"
        }, headers=auth_headers)
        assert resp.status_code == 200
        conv_id = resp.json()["data"]["id"]

        # Post message
        resp = await client.post(f"/conversations/{conv_id}/messages", json={
            "conversation_id": conv_id,
            "content": "Hello from integration test"
        }, headers=auth_headers)
        assert resp.status_code == 200

        # Get messages
        resp = await client.get(f"/conversations/{conv_id}/messages", headers=auth_headers)
        assert resp.status_code == 200
        msgs = resp.json()["data"]
        assert len(msgs) >= 1
        assert msgs[0]["content"] == "Hello from integration test"


class TestAuth:
    async def test_full_auth_flow(self, client):
        # Login
        resp = await client.post("/auth/login", json={
            "username": "factory_admin", "password": "admin123"
        })
        assert resp.status_code == 200
        access = resp.json()["data"]["access_token"]
        refresh = resp.json()["data"]["refresh_token"]

        # Use access token
        headers = {"Authorization": f"Bearer {access}"}
        resp = await client.get("/alerts", headers=headers)
        assert resp.status_code == 200

        # Refresh
        resp = await client.post("/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 200
        new_access = resp.json()["data"]["access_token"]

        # Verify new access works
        headers = {"Authorization": f"Bearer {new_access}"}
        resp = await client.get("/alerts", headers=headers)
        assert resp.status_code == 200