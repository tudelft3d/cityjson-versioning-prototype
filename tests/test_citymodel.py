import cityjson.citymodel as citymodel

class TestCityJSON:
    """Class that tests CityJSON class."""

    def test_load_cityjson(self):
        """Tests if the CityJSON class loads the file correctly."""

        cm = citymodel.CityJSON.from_file("Examples/rotterdam/initial.json")

        assert cm["version"] == "1.0"
        print(cm.cityobjects)

    def test_empty_cityjson(self):
        """Initialising CityJSON without arguments should return minimal
        CityJSON.
        """

        cm = citymodel.CityJSON()
        assert cm.data == citymodel.min_cityjson

    def test_applying_transform(self):
        """Tests whether setting the transform updates all vertices as
        necessary.
        """
        cm = citymodel.CityJSON()

        # This is hacky. You shouldn't update vertices manually and then prepare
        # the cache yourself, but it's only done for testing purposes here.
        cm["vertices"] = [[1001, 1001, 1001],
                          [1002, 1002, 1002],
                          [1003, 1003, 1003],
                          [1004, 1004, 1004]]

        cm._vertex_handler.prepare_cache()
        cm.set_transform([1000, 1000, 1000], [0.001, 0.001, 0.001])

        assert len(cm["vertices"]) == 4
        assert cm["vertices"][0] == [1000, 1000, 1000]
        assert cm["vertices"][1] == [2000, 2000, 2000]

class TestIndexedVerticesHandler:
    """Tests the IndexedVerticesHandler class."""

    def test_vertex_dereference(self):
        """Test if the vertices are deferenced properly."""
        cm = citymodel.CityJSON()

        cm["vertices"] = [[1, 1, 1],
                          [2, 2, 2],
                          [3, 3, 3],
                          [4, 4, 4]]

        handler = citymodel.IndexedVerticesHandler(cm)

        obj = citymodel.CityObject({"geometry": [{
                    "boundaries": [[[0, 1, 2, 3]]]
                }]
            })

        new_obj = handler.dereference(obj)
        for i, vertex in enumerate(new_obj["geometry"][0]["boundaries"][0][0]):
            assert isinstance(vertex, list)
            assert vertex == [i+1, i+1, i+1]

    def test_vertex_reference(self):
        """Test if the vertices are references properly."""
        cm = citymodel.CityJSON()

        cm["vertices"] = [[1, 1, 1],
                          [2, 2, 2],
                          [3, 3, 3],
                          [4, 4, 4]]

        handler = citymodel.IndexedVerticesHandler(cm)

        obj = citymodel.CityObject({"geometry": [{
                    "boundaries": [[[[1, 1, 1],
                                     [2, 2, 2],
                                     [3, 3, 3],
                                     [4, 4, 4]]]]
                }]
            })

        new_obj = handler.reference(obj)
        for i, vertex in enumerate(new_obj["geometry"][0]["boundaries"][0][0]):
            assert isinstance(vertex, int)
            assert vertex == i
        
        obj = citymodel.CityObject({"geometry": [{
                    "boundaries": [[[[1, 1, 1],
                                     [2, 2, 2],
                                     [3, 3, 3],
                                     [5, 5, 5]]]]
                }]
            })

        new_obj = handler.reference(obj)
        assert isinstance(new_obj["geometry"][0]["boundaries"][0][0][3], int)
        assert new_obj["geometry"][0]["boundaries"][0][0][3] == 4

    def test_update_vertices(self):
        """Test if the vertices of the citymodel are updated properly."""
        cm = citymodel.CityJSON()

        cm["vertices"] = [[1, 1, 1],
                          [2, 2, 2],
                          [3, 3, 3],
                          [4, 4, 4]]

        handler = citymodel.IndexedVerticesHandler(cm)
        handler.update_vertex_list()

        assert len(cm["vertices"]) == 4
        assert cm["vertices"][0] == [1, 1, 1]

        cm["vertices"] = [[1, 1, 1],
                          [2, 2, 2],
                          [2, 2, 2],
                          [4, 4, 4]]

        handler = citymodel.IndexedVerticesHandler(cm)
        handler.update_vertex_list()

        assert len(cm["vertices"]) == 3
        assert cm["vertices"][0] == [1, 1, 1]

    def test_update_vertices_with_transform(self):
        """Test if the vertices of the city model are updated properly when
        transform is present.
        """
        cm = citymodel.CityJSON()

        cm["vertices"] = [[1, 1, 1],
                          [2, 2, 2],
                          [3, 3, 3],
                          [4, 4, 4]]

        handler = citymodel.IndexedVerticesHandler(cm)
        handler.update_vertex_list()

        assert len(cm["vertices"]) == 4
        assert cm["vertices"][0] == [1, 1, 1]

        cm["vertices"] = [[1, 1, 1],
                          [2, 2, 2],
                          [2, 2, 2],
                          [4, 4, 4]]

        handler = citymodel.IndexedVerticesHandler(cm)
        handler.update_vertex_list()

        assert len(cm["vertices"]) == 3
        assert cm["vertices"][0] == [1, 1, 1]
