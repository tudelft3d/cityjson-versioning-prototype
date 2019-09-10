import pytest
from citymodel.geometry import vertices_from_tuple, Vertex, LinearRing, Surface, MultiSurface, Shell, Solid, MultiSolid, GeometryObject, SemanticSurface

# Testing coordinates for a floor surface
floor_coords = ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0))
floor_hole_coords = ((0.2, 0.2, 0), (0.2, 0.8, 0), (0.8, 0.8, 0), (0.8, 0.2, 0))

# Testing coordinates for a roof surface
roof_coords = ((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1))
roof_hole_coords = ((0.2, 0.2, 1), (0.2, 0.8, 1), (0.8, 0.8, 1), (0.8, 0.2, 1))

class TestVertex:
    """Tests related to the Vertex class"""

    def test_equality(self):
        """Is vertex initialised correctly by all possible ways?"""

        assert Vertex(0, 0, 0) == Vertex(0, 0, 0)
        assert Vertex(0, 0, 0) == Vertex(0.0, 0, 0)
        # Test vertex from list
        assert Vertex(0, 0, 0) == Vertex([0, 0, 0])
        # Test vertex from tuple
        assert Vertex(0, 0, 0) == Vertex((0, 0, 0))
    
    def test_addition(self):
        """Is vertex addition working?"""

        added_vertex = Vertex(1, 1, 1) + Vertex(1, 2, 3)
        assert added_vertex == Vertex(2, 3, 4)
    
    def test_subtraction(self):
        """Is vertex subtraction working?"""

        subtracted_vertex = Vertex(3, 4, 5) - Vertex(1, 3, 2)
        assert subtracted_vertex == Vertex(2, 1, 3)

    def test_vertices_from_tuples_function(self):
        """Is the vertex_from_tuples helper function working?"""

        vertices = vertices_from_tuple(((0, 0, 0), (0, 1, 0)))

        assert len(vertices) == 2

        assert vertices[0] == Vertex(0, 0, 0)
        assert vertices[1] == Vertex(0, 1, 0)

class TestLinearRing:
    """Tests related to the LinearRing class"""

    def test_create_simple(self):
        """Is a linear ring created as expected?"""

        ring = LinearRing(floor_coords)

        assert len(ring.vertices) == 4
        assert all([isinstance(v, Vertex) for v in ring.vertices])

class TestSurface:
    """Tests related to the Surface class"""

    def test_create_from_coords(self):
        """Is a simple surface (without holes) created as expected?"""

        surface = Surface([floor_coords])

        assert len(surface.boundaries) == 1
        assert isinstance(surface.boundaries[0], LinearRing)
        assert surface.has_holes() == False
    
    def test_create_from_coords_with_holes(self):
        """Is a simple surface (with holes) created as expected?"""
        
        outer_ring = LinearRing(floor_coords)
        hole_ring = LinearRing(floor_hole_coords)
        
        surface = Surface([outer_ring, hole_ring])

        assert len(surface.boundaries) == 2
        for ring in surface.boundaries:
            assert isinstance(ring, LinearRing)
        assert surface.has_holes() == True

class TestMultiSurface:
    """Tests related to the MultiSurface class"""

    def test_create_from_coords(self):
        """Is a multi-surface created from coordinates?"""

        multisurface = MultiSurface([
            [floor_coords],
            [roof_coords]
        ])

        assert isinstance(multisurface, MultiSurface)
        assert len(multisurface.surfaces) == 2
        for surface in multisurface.surfaces:
            assert isinstance(surface, Surface)
            assert surface.has_holes() == False
        
    def test_create_from_coords_with_holes(self):
        """Is a multi-surface created from coordinates?"""

        multisurface = MultiSurface([
            [floor_coords, floor_hole_coords],
            [roof_coords, roof_hole_coords]
        ])

        assert isinstance(multisurface, MultiSurface)
        assert len(multisurface.surfaces) == 2
        for surface in multisurface.surfaces:
            assert isinstance(surface, Surface)
            assert surface.has_holes() == True
    
    def test_create_from_surfaces(self):
        """Is a multi-surface created from surfaces?"""

        floor = Surface([floor_coords])
        roof = Surface([roof_coords, roof_hole_coords])

        multisurface = MultiSurface([floor, roof])

        assert isinstance(multisurface, MultiSurface)
        assert len(multisurface.surfaces) == 2
        for surface in multisurface.surfaces:
            assert isinstance(surface, Surface)
        assert multisurface.surfaces[0].has_holes() == False
        assert multisurface.surfaces[1].has_holes() == True
    
class TestShell:
    """Tests related to the Shell class"""

    def test_create_from_coords(self):
        """Is a multi-surface created from coordinates?"""

        multisurface = Shell([
            [floor_coords],
            [roof_coords]
        ])

        assert isinstance(multisurface, Shell)
        assert len(multisurface.surfaces) == 2
        for surface in multisurface.surfaces:
            assert isinstance(surface, Surface)
            assert surface.has_holes() == False
        
    def test_create_from_coords_with_holes(self):
        """Is a multi-surface created from coordinates?"""

        multisurface = Shell([
            [floor_coords, floor_hole_coords],
            [roof_coords, roof_hole_coords]
        ])

        assert isinstance(multisurface, Shell)
        assert len(multisurface.surfaces) == 2
        for surface in multisurface.surfaces:
            assert isinstance(surface, Surface)
            assert surface.has_holes() == True
    
    def test_create_from_surfaces(self):
        """Is a multi-surface created from surfaces?"""

        floor = Surface([floor_coords])
        roof = Surface([roof_coords, roof_hole_coords])

        multisurface = Shell([floor, roof])

        assert isinstance(multisurface, Shell)
        assert len(multisurface.surfaces) == 2
        for surface in multisurface.surfaces:
            assert isinstance(surface, Surface)
        assert multisurface.surfaces[0].has_holes() == False
        assert multisurface.surfaces[1].has_holes() == True

class TestSolid:
    """Tests related to the Solid class"""

    def test_create_from_coords(self):
        """Is a Solid created from coords?"""

        solid = Solid([
            [[floor_coords], [roof_coords]]
        ])

        assert isinstance(solid, Solid)
        assert len(solid.shells) == 1
        assert isinstance(solid.shells[0], Shell)
        assert len(solid.shells[0].surfaces) == 2

    def test_create_from_shells(self):
        """Is a Solid created from Shells?"""

        shell = Shell([
            [floor_coords],
            [roof_coords]
        ])

        solid = Solid([shell])

        assert isinstance(solid, Solid)
        assert len(solid.shells) == 1
        assert isinstance(solid.shells[0], Shell)
        assert len(solid.shells[0].surfaces) == 2

class TestMultiSolid:
    """Tests related to the MultiSolid class"""

    def test_create_from_coords(self):
        """Is a MultiSolid created from coords?"""

        multisolid = MultiSolid([
            [[[floor_coords]]],
            [[[roof_coords]]]
        ])

        assert isinstance(multisolid, MultiSolid)
        assert len(multisolid.solids) == 2
        for solid in multisolid.solids:
            assert isinstance(solid, Solid)
            assert len(solid.shells) == 1
            assert len(solid.shells[0].surfaces) == 1

class TestSemanticSurface:
    """Tests related to the SemanticSurface class"""

    def test_create_wall_surface(self):
        """Is a wall surface created as expected?"""

        semanticsurface = SemanticSurface("WallSurface")

        assert isinstance(semanticsurface, SemanticSurface)
        assert semanticsurface.surface_type == "WallSurface"

class TestGeometryObject:
    """Tests related to the GeometryObject class"""

    def test_create_simple_surface(self):
        """Is a GeometryObject with a Surface created as expected?"""

        surface = Surface([floor_coords])
        geom = GeometryObject(1, surface)

        assert isinstance(geom, GeometryObject)
        assert isinstance(geom.boundaries, Surface)
        assert geom.lod == 1
    
    def test_multisurface_semantic_surfaces(self):
        """Are semantic surfaces of a multi-surface returned as expected?"""

        floor = Surface([floor_coords], SemanticSurface("FloorSurface"))
        roof = Surface([roof_coords], SemanticSurface("RoofSurface"))

        multisurface = MultiSurface([floor, roof])
        geom = GeometryObject(1, multisurface)

        assert len(multisurface.boundaries) == 2
        assert len(geom.semantic_surfaces) == 2
        for surface in geom.semantic_surfaces:
            assert isinstance(surface, SemanticSurface)
    
    def test_solid_semantic_surfaces(self):
        """Are semantic surfaces of a solid returned as expected?"""

        floor = Surface([floor_coords], SemanticSurface("FloorSurface"))
        roof = Surface([roof_coords], SemanticSurface("RoofSurface"))

        solid = Solid([[floor, roof]])
        geom = GeometryObject(1, solid)

        assert len(geom.semantic_surfaces) == 2
        for surface in geom.semantic_surfaces:
            assert isinstance(surface, SemanticSurface)
    
    def test_unique_semantic_surfaces(self):
        """Are semantic surfaces of a solid returned as expected?"""

        floor_surface = SemanticSurface("FloorSurface")
        floor = Surface([floor_coords], floor_surface)
        second_floor = Surface([floor_hole_coords], floor_surface)
        roof = Surface([roof_coords], SemanticSurface("RoofSurface"))

        solid = Solid([[floor, second_floor, roof]])
        geom = GeometryObject(1, solid)

        assert len(geom.semantic_surfaces) == 2
        for surface in geom.semantic_surfaces:
            assert isinstance(surface, SemanticSurface)