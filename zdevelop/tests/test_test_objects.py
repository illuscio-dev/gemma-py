from gemma.test_objects import test_objects, DataSimple, DataTarget, DataStructured


def test_make_test_objects():
    simple, data_dict, data_list, structured, target = test_objects()

    assert isinstance(data_dict, dict)
    assert isinstance(data_list, list)
    assert isinstance(simple, DataSimple)
    assert isinstance(structured, DataStructured)
    assert isinstance(target, DataTarget)


def test_values():
    simple, data_dict, data_list, structured, target = test_objects()

    assert data_list[-1].text == "in a list"
    assert data_list[-1].number == 20

    assert data_dict["a"] == "a dict"
    assert data_dict[2] == "two dict"
    assert data_dict["nested"]["one key"] == 1

    assert structured.a == "a data"
    assert structured.dict_data[1] == "one dict"
