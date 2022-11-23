import pytest

from common_utils.constants import POTENTIAL_SIMULATION_STATUS, USER_ROLE
from common_utils.exceptions import DBException, DBNotFoundException
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    PotentialSimulationDBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
    SlamSimulationDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
    UserDBHandler,
    get_db_handlers,
)
from tests.constants import CLIENT_ID_1, TEST_CLIENT_NAME
from tests.db_fixtures import login_as


class TestDBHandlers:
    def test_add_client_default_db_values(self):
        client = ClientDBHandler.add(name="test")
        for key in ("id", "created", "updated", "logo_gcs_link"):
            client.pop(key)
        assert client == {
            "name": "test",
            "option_dxf": True,
            "option_pdf": True,
            "option_analysis": True,
            "option_competition": False,
            "option_ifc": True,
        }

    def test_get_client_by_id(self, client_db):
        client_id = client_db["id"]
        client_from_db = ClientDBHandler.get_by(id=client_id)
        assert client_from_db is not None
        assert client_from_db == client_db

    def test_get_client_by_site_id(self, client_db, site, make_sites, make_clients):
        generated_clients = make_clients(3)
        generated_sites = make_sites(*generated_clients)
        client_from_db = ClientDBHandler.get_by_site_id(site_id=site["id"])
        assert client_from_db == client_db
        for generated_site, generated_client in zip(generated_sites, generated_clients):
            assert (
                ClientDBHandler.get_by_site_id(site_id=generated_site["id"])["id"]
                == generated_client["id"]
            )

    def test_find_client(self, client_db):
        name = TEST_CLIENT_NAME
        clients = ClientDBHandler.find(name=name)
        assert clients is not None
        assert clients[0] == client_db

    def test_update_unexisting_entity(self, client_db):
        with pytest.raises(DBNotFoundException):
            ClientDBHandler.update({"id": 9999999}, {"name": "a good client"})

    def test_add_new_client_with_pk(self, client_db):
        with pytest.raises(DBException):
            ClientDBHandler.add(**client_db)

    def test_update_client(self, client_db):
        client_id = client_db["id"]
        updated_client = ClientDBHandler.update(
            {"id": client_id}, {"name": "a good client"}
        )
        assert updated_client is not None
        assert updated_client["name"] == "a good client"

    def test_delete_client_by_id(self, client_db):
        client_id = client_db["id"]
        ClientDBHandler.delete({"id": client_id})
        with pytest.raises(DBNotFoundException):
            assert SiteDBHandler.get_by(id=client_id)

    def test_get_site_by_id(self, site):
        site_id = site["id"]
        site_from_db = SiteDBHandler.get_by(id=site_id)
        assert site_from_db is not None
        assert site_from_db == site

    def test_find_site(self, site):
        region = "Switzerland"
        sites = SiteDBHandler.find(region=region)
        assert sites is not None
        assert sites[0] == site

    def test_update_site(self, site):
        site_id = site["id"]
        updated_site = SiteDBHandler.update(
            {"id": site_id}, {"name": "Moderate-sized portfolio"}
        )
        assert updated_site.pop("name") == "Moderate-sized portfolio"
        del site["name"]
        del site["updated"]
        del updated_site["updated"]
        assert updated_site == site

    def test_add_new_site_with_pk(self, site):
        with pytest.raises(DBException):
            SiteDBHandler.add(**site)

    def test_delete_site_by_id(self, site):
        site_id = site["id"]
        SiteDBHandler.delete({"id": site_id})
        with pytest.raises(DBNotFoundException):
            assert SiteDBHandler.get_by(id=site_id)

    def test_successful_deletion_of_site_with_simulation(self, site):
        SlamSimulationDBHandler.add(run_id="1", site_id=site["id"], type="VIEW_SUN")
        SiteDBHandler.delete(item_pk={"id": site["id"]})
        with pytest.raises(DBNotFoundException):
            assert SiteDBHandler.get_by(id=site["id"])

    def test_get_floor_by_id(self, floor):
        floor_id = floor["id"]
        floor_from_db = FloorDBHandler.get_by(id=floor_id)
        assert floor_from_db is not None
        assert floor_from_db == floor

    def test_find_floor(self, floor):
        floor_number = 1
        floors = FloorDBHandler.find(floor_number=floor_number)
        assert floors is not None
        assert floors[0] == floor

    def test_update_floor(self, plan, floor, building):
        floor_id = floor["id"]
        updated_floor = FloorDBHandler.update({"id": floor_id}, {"floor_number": 13})
        assert updated_floor is not None
        assert updated_floor["plan_id"] == plan["id"]
        assert updated_floor["building_id"] == building["id"]
        assert updated_floor["floor_number"] == 13

    def test_delete_floor_by_id(self, floor):
        floor_id = floor["id"]
        FloorDBHandler.delete({"id": floor_id})
        with pytest.raises(DBNotFoundException):
            assert FloorDBHandler.get_by(id=floor_id)

    def test_delete_floor_deletes_related_units_but_not_areas(
        self, floor, unit, areas_db
    ):
        plan_id = floor["plan_id"]
        FloorDBHandler.delete({"id": floor["id"]})
        with pytest.raises(DBNotFoundException):
            FloorDBHandler.get_by(id=floor["id"])
        assert [] == UnitDBHandler.find(plan_id=plan_id)
        assert AreaDBHandler.find(plan_id=plan_id)

    def test_delete_building_deletes_related_floor_plan_units_and_areas_but_not_site(
        self, floor, unit, areas_db
    ):
        plan_id = floor["plan_id"]
        building_id = floor["building_id"]
        site_id = unit["site_id"]

        BuildingDBHandler.delete({"id": building_id})

        with pytest.raises(DBNotFoundException):
            BuildingDBHandler.get_by(id=building_id)
        with pytest.raises(DBNotFoundException):
            FloorDBHandler.get_by(id=floor["id"])
        with pytest.raises(DBNotFoundException):
            PlanDBHandler.get_by(id=plan_id)
        assert [] == UnitDBHandler.find(plan_id=plan_id)
        assert [] == AreaDBHandler.find(plan_id=plan_id)
        assert site_id == SiteDBHandler.get_by(id=site_id)["id"]

    def test_get_plan_by_id(self, plan):
        plan_id = plan["id"]
        plan_from_db = PlanDBHandler.get_by(id=plan_id)
        assert plan_from_db is not None
        assert plan_from_db == plan

    def test_add_new_plan_with_pk(self, plan):
        with pytest.raises(DBException):
            PlanDBHandler.add(**plan)

    def test_update_plan(self, plan):
        update_data = dict(
            default_wall_height=3.0,
            default_window_lower_edge=0.3,
            default_window_upper_edge=2.8,
        )
        plan_id = plan["id"]
        plan_from_db = PlanDBHandler.update({"id": plan_id}, update_data)
        assert (
            plan_from_db["default_window_lower_edge"]
            == update_data["default_window_lower_edge"]
        )
        assert (
            plan_from_db["default_window_upper_edge"]
            == update_data["default_window_upper_edge"]
        )
        assert plan_from_db["default_wall_height"] == update_data["default_wall_height"]
        assert plan_from_db["id"] == plan["id"]

    def test_select_plan(self, plan):
        plan_from_db = PlanDBHandler.find(default_wall_height=2.6)
        assert isinstance(plan_from_db, list)
        assert len(plan_from_db) == 1
        assert plan_from_db[0] == plan

    def test_delete_plan(self, plan):
        plan_id = plan["id"]
        PlanDBHandler.delete({"id": plan_id})
        with pytest.raises(DBNotFoundException):
            assert PlanDBHandler.get_by(id=plan_id)

    def test_delete_non_existing_plan_raises(self):
        with pytest.raises(DBNotFoundException):
            PlanDBHandler.delete({"id": 9999})

    def test_get_unit_by_id(self, unit):
        unit_id = unit["id"]
        unit_from_db = UnitDBHandler.get_by(id=unit_id)
        assert unit_from_db is not None
        assert unit_from_db == unit

    def test_find_unit(self, unit):
        unit_from_db = UnitDBHandler.find(client_id=CLIENT_ID_1)
        assert unit_from_db is not None
        assert unit_from_db[0] == unit

    def test_update_unit(self, unit, floor):
        client_id = "XX2013"
        apartment_no = 13
        plan_from_db = UnitDBHandler.update(
            {"id": unit["id"]}, {"client_id": client_id, "apartment_no": apartment_no}
        )
        assert plan_from_db is not None
        assert plan_from_db["floor_id"] == floor["id"]
        assert plan_from_db["apartment_no"] == apartment_no
        assert plan_from_db["client_id"] == client_id

    def test_plans_from_site_id(self, site, plan):
        db_plans = PlanDBHandler.find(site_id=site["id"])
        assert (
            len([db_plan for db_plan in db_plans if db_plan["id"] == plan["id"]]) == 1
        )

    def test_update_plan_with_georeference_data(self, plan):
        georef = {
            "georef_x": 7.43858096801,
            "georef_y": 49.6480052296,
            "georef_scale": 1.05,
            "georef_rot_angle": 0.5,
            "georef_rot_x": 0,
            "georef_rot_y": 0,
        }
        PlanDBHandler.update(item_pks={"id": plan["id"]}, new_values=georef)
        db_plan = PlanDBHandler.get_by(id=plan["id"])
        assert georef["georef_y"] == db_plan["georef_y"]

    def test_update_floor_with_georeference_data(self, floor):
        georef_z = {"georef_z": 423}
        FloorDBHandler.update(item_pks={"id": floor["id"]}, new_values=georef_z)
        db_floor = FloorDBHandler.get_by(id=floor["id"])
        assert db_floor["georef_z"] == georef_z["georef_z"]

    def test_update_building_with_elevation_data(self, building):
        elevation = {"elevation": 413}
        BuildingDBHandler.update(item_pks={"id": building["id"]}, new_values=elevation)
        db_building = BuildingDBHandler.get_by(id=building["id"])
        assert db_building["elevation"] == elevation["elevation"]

    @pytest.mark.parametrize("filter_ground_floor", [True, False])
    def test_get_floors_by_site_id(
        self,
        client_db,
        site_coordinates,
        random_media_link,
        site_region_proj_ch,
        filter_ground_floor,
    ):
        sites = [
            SiteDBHandler.add(
                client_id=client_db["id"],
                name=f"Big-ass portfolio {i}",
                region="Switzerland",
                **site_region_proj_ch,
                **site_coordinates,
            )
            for i in range(3)
        ]

        buildings = [
            BuildingDBHandler.add(
                site_id=site["id"],
                housenumber=str(i),
                city="Zurich",
                zipcode="8000",
                street="Technoparkstrasse",
            )
            for site in sites
            for i in range(3)
        ]

        plans = [
            PlanDBHandler.add(
                default_wall_height=2.6,
                default_window_lower_edge=0.25,
                default_window_upper_edge=2.4,
                site_id=building["site_id"],
                building_id=building["id"],
                image_hash=f'{building["id"]}',
                image_mime_type="jpeg",
                image_height=200,
                image_width=200,
                image_gcs_link=random_media_link,
            )
            for building in buildings
        ]

        floors = [
            FloorDBHandler.add(
                plan_id=plan["id"], building_id=plan["building_id"], floor_number=i
            )
            for plan in plans
            for i in range(3)
        ]

        # There are 3 sites:
        # - 3 buildings per site
        #   - 1 plan per building
        #       - 3 floors per plan

        assert len(floors) == 3**3

        for site in sites:
            if filter_ground_floor:
                num_floors = len(
                    FloorDBHandler.find_by_site_id(site_id=site["id"], floor_number=0)
                )
                assert num_floors == 3  # 3 buildings
            else:
                assert len(FloorDBHandler.find_by_site_id(site_id=site["id"])) == 3 * 3

    def test_update_simulation(self, potential_db_simulation_ch_sun_empty):
        new_status = POTENTIAL_SIMULATION_STATUS.SUCCESS
        updated_simulation = PotentialSimulationDBHandler.update(
            item_pks=dict(id=potential_db_simulation_ch_sun_empty["id"]),
            new_values=dict(status=new_status),
        )
        assert updated_simulation.pop("status") == new_status.value
        updated_simulation.pop("updated")
        for k, v in potential_db_simulation_ch_sun_empty.items():
            if k in updated_simulation:
                assert updated_simulation[k] == v, k

    def test_site_constraint(
        self,
        client_db,
        site_coordinates,
        site_region_proj_ch,
    ):
        SiteDBHandler.add(
            client_id=client_db["id"],
            name="Big-ass portfolio",
            region="Switzerland",
            client_site_id="blah",
            **site_coordinates,
            **site_region_proj_ch,
        )
        with pytest.raises(DBException):
            SiteDBHandler.add(
                client_id=client_db["id"],
                name="Big-ass portfolio",
                region="Switzerland",
                client_site_id="blah",
                **site_coordinates,
                **site_region_proj_ch,
            )

    def test_find_in_group(self, make_clients):
        num_clients = 3
        clients = make_clients(num_clients)
        assert not list(ClientDBHandler.find_in(id=[]))
        client_ids = [client["id"] for client in clients]
        assert len(list(ClientDBHandler.find_in(id=client_ids))) == num_clients
        assert len(list(ClientDBHandler.find_in(id=client_ids[0:1]))) == 1
        assert {
            client["name"]
            for client in ClientDBHandler.find_in(
                id=client_ids, output_columns=["name"]
            )
        } == {x["name"] for x in clients}

    def test_get_number_of_units_by_client_sites(
        self, client_db, site_with_full_slam_results_success, unit
    ):
        result = ClientDBHandler.get_total_unit_number_by_site_id_completed(
            client_id=client_db["id"]
        )
        assert result == {site_with_full_slam_results_success["id"]: 1}

    def test_get_number_of_units_by_client_sites_should_include_maisonettes(
        self, client_db, site_with_full_slam_results_success, unit
    ):
        UnitDBHandler.add(
            site_id=site_with_full_slam_results_success["id"],
            plan_id=unit["plan_id"],
            floor_id=unit["floor_id"],
            apartment_no=1,
            client_id=CLIENT_ID_1,
        )
        result = ClientDBHandler.get_total_unit_number_by_site_id_completed(
            client_id=client_db["id"]
        )
        assert result == {site_with_full_slam_results_success["id"]: 1}

    def test_get_number_of_units_by_client_sites_zero_units(
        self, client_db, site_with_full_slam_results_success
    ):
        result = ClientDBHandler.get_total_unit_number_by_site_id_completed(
            client_id=client_db["id"]
        )
        assert result == {site_with_full_slam_results_success["id"]: 0}

    def test_get_number_of_units_by_client_sites_zero_sites(self, client_db):
        result = ClientDBHandler.get_total_unit_number_by_site_id_completed(
            client_id=client_db["id"]
        )
        assert result == {}

    def test_delete_area_fk_propagates_correctly(self, areas_db, unit):
        area_ids = [area["id"] for area in areas_db]
        for area_id in area_ids:
            UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area_id)

        AreaDBHandler.delete_in(id=area_ids)

        assert len(UnitAreaDBHandler.find()) == 0
        assert len(AreaDBHandler.find()) == 0


class TestUserHandler:
    @staticmethod
    def test_user_handler_add_user_with_roles():
        added_user = UserDBHandler.add(
            name="Testuser",
            login="testlogin",
            password="testpassword",
            roles=[USER_ROLE.TEAMMEMBER],
            email="test@fake.com",
        )
        assert added_user.get("roles")[0] == USER_ROLE.TEAMMEMBER
        assert added_user.get("login") == "testlogin"
        assert added_user.get("name") == "Testuser"
        assert added_user.get("password") is None
        assert added_user.get("created") is not None

    @staticmethod
    def test_user_unique_constraint():
        UserDBHandler.add(
            name="Testuser",
            login="testlogin",
            password="testpassword",
            roles=[USER_ROLE.TEAMMEMBER],
            email="test@fake.com",
        )
        with pytest.raises(
            DBException,
            match='duplicate key value violates unique constraint "users_email_key"',
        ):
            UserDBHandler.add(
                name="Testuser",
                login="testlogin123",
                password="testpassword123",
                roles=[USER_ROLE.TEAMMEMBER],
                email="test@fake.com",
            )

    @staticmethod
    def test_user_unique_constraint_case_insensitive():
        UserDBHandler.add(
            name="Testuser",
            login="testlogin",
            password="testpassword",
            roles=[USER_ROLE.TEAMMEMBER],
            email="TEST@fake.com",
        )
        with pytest.raises(
            DBException,
            match='duplicate key value violates unique constraint "users_email_key"',
        ):
            UserDBHandler.add(
                name="Testuser",
                login="testlogin123",
                password="testpassword123",
                roles=[USER_ROLE.TEAMMEMBER],
                email="test@fake.com",
            )

    @staticmethod
    @login_as(["TEAMMEMBER"])
    def test_user_handler_get_slam_user_password_verified(login):
        user = UserDBHandler.get_user_password_verified(
            user=login["user"]["login"], password=login["user"]["password"]
        )
        assert user is not None
        UserDBHandler.update(
            item_pks={"id": user["id"]}, new_values={"name": "Payaso TEAMMEMBER"}
        )
        user_after_update = UserDBHandler.get_user_password_verified(
            user=login["user"]["login"], password=login["user"]["password"]
        )
        assert user_after_update is not None


def test_get_db_handlers_finds_all_db_handlers():
    import handlers.db
    from handlers.db import BaseDBHandler

    exported_handlers = handlers.db.__all__
    discovered_handlers = [
        handler.__name__ for handler in get_db_handlers(BaseDBHandler)
    ]
    assert set(exported_handlers) == set(discovered_handlers)


def test_excluded_entity_attributes_are_not_serialized(
    site,
    building,
    floor,
    plan,
    unit,
    potential_db_simulation_ch_sun_empty,
    annotations_finished,
    areas_db,
):
    from handlers.db import BaseDBHandler

    for handler_subclass in BaseDBHandler.__subclasses__():
        exclusions = handler_subclass.schema.exclude
        if exclusions:
            instance = handler_subclass.find()[0]
            assert all(k not in exclusions for k in instance.keys())


def test_floor_handler_cascade_delete(floor, unit):
    # Given 1 floor, 1 unit, 1 plan and 1 annotation exist in the db

    # When calling FloorDBHandler.delete

    FloorDBHandler.delete(item_pk=dict(id=unit["floor_id"]))

    # Then the floor should get deleted from the database
    assert len(FloorDBHandler.find()) == 0

    # And the related units should get deleted as well
    assert len(UnitDBHandler.find()) == 0


def test_delete_plan_cascade_works_correctly(
    floor, unit, annotations_finished, areas_db
):
    PlanDBHandler.delete(item_pk={"id": floor["plan_id"]})
    assert not FloorDBHandler.find()
    assert not UnitDBHandler.find()
    assert not ReactPlannerProjectsDBHandler.find()
    assert not AreaDBHandler.find()


def test_created_updated_change_each_time():
    client1 = ClientDBHandler.add(name="Client Papaya")
    client2 = ClientDBHandler.add(name="Client Payaso")
    assert client1["created"] != client2["created"]

    ClientDBHandler.update(
        item_pks={"id": client1["id"]}, new_values={"name": "Client carapapa"}
    )
    ClientDBHandler.update(
        item_pks={"id": client2["id"]}, new_values={"name": "new name"}
    )
    clients = ClientDBHandler.find()
    assert clients[0]["updated"] != clients[1]["updated"]
