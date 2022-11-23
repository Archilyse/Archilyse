from handlers import QAHandler
from handlers.db import QADBHandler
from handlers.db.qa_handler import (
    INDEX_ANF_AREA,
    INDEX_HNF_AREA,
    INDEX_NET_AREA,
    INDEX_ROOM_NUMBER,
)


def test_site_wo_units_generates_empty_report(mocker):
    from handlers.ph_vector import PHResultVectorHandler

    default_value = 0.0
    client_id = "client_id_1"

    mocker.patch.object(
        QADBHandler,
        "get_by",
        return_value={
            "data": {
                client_id: {
                    key: default_value
                    for key in (
                        INDEX_ROOM_NUMBER,
                        INDEX_NET_AREA,
                        INDEX_HNF_AREA,
                        INDEX_ANF_AREA,
                    )
                }
            }
        },
    )
    mocker.patch.object(
        PHResultVectorHandler,
        "basic_features",
        mocker.PropertyMock(return_value={}),
    )
    report = QAHandler(site_id=123).generate_qa_report()
    assert report.to_dict() == {
        "number_of_rooms": {client_id: default_value},
        "net_area": {client_id: default_value},
        "HNF": {client_id: default_value},
        "ANF": {client_id: default_value},
    }


def test_site_wo_qa_data_and_no_units_generates_empty_report(mocker):
    from handlers.ph_vector import PHResultVectorHandler

    mocker.patch.object(
        QADBHandler,
        "get_by",
        return_value={"data": {}},
    )
    mocker.patch.object(
        PHResultVectorHandler,
        "basic_features",
        mocker.PropertyMock(return_value={}),
    )
    report = QAHandler(site_id=123).generate_qa_report()
    assert report.to_dict() == {
        "number_of_rooms": {},
        "net_area": {},
        "HNF": {},
        "ANF": {},
    }
