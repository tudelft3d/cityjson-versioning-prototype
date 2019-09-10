"""A module that describes the geometric data model of a 3D city model"""

from typing import Dict, List, Tuple

class GeometryObject:
    """Defines the basic functionality of a geometry"""

    def __init__(self, lod, boundaries=None):
        self._lod = lod
        self._boundaries = boundaries

    @property
    def lod(self):
        return self._lod
    
    @lod.setter
    def lod(self, value):
        self._lod = value
    
    @property
    def boundaries(self):
        return self._boundaries
    
    @property
    def semantic_surfaces(self):
        result = []
        def get_semantics(surface):
            if isinstance(surface, Surface):
                if surface.semantics not in result:
                    result.append(surface.semantics)
            else:
                for boundary in surface.boundaries:
                    get_semantics(boundary)
        get_semantics(self._boundaries)
        return result

class SemanticSurface:
    """Describes the semantic surfaces of a geometry object"""
    
    def __init__(self, surface_type=None, attributes=None):
        self._surface_type = surface_type
        self._attributes = attributes
    
    @property
    def surface_type(self):
        return self._surface_type

class MultiSolid:
    """Describes a set of solids"""

    def __init__(self, solids=[]):
        self._solids = []
        if solids is not None:
            for solid in solids:
                if isinstance(solid, Solid):
                    self._solids.append(solid)
                else:
                    self._solids.append(Solid(solid))

    @property
    def solids(self):
        return self._solids
    
    @property
    def boundaries(self):
        return self._solids

class Solid:
    """Describes a solid geometry"""

    def __init__(self, shells=[]):
        self._shells = []
        if shells is not None:
            for shell in shells:
                if isinstance(shell, Shell):
                    self._shells.append(shell)
                else:
                    self._shells.append(Shell(shell))
    
    @property
    def shells(self):
        return self._shells

    @property
    def boundaries(self):
        return self._shells

class MultiSurface:
    """Describe a multi-surface geometry"""

    def __init__(self, surfaces=[]):
        self._surfaces = []
        if surfaces is not None:
            for surface in surfaces:
                if isinstance(surface, Surface):
                    self._surfaces.append(surface)
                else:
                    self._surfaces.append(Surface(surface))
    
    @property
    def surfaces(self):
        return self._surfaces

    @property
    def boundaries(self):
        return self._surfaces

class CompositeSurface(MultiSurface):
    """Describes a composite-surface geometry (similar to multi-surface)"""
    pass

class Shell(MultiSurface):
    """Describes a shell of a solid

    This must be used for the description of solids
    """
    pass

class Surface:
    """Describes a surface"""

    def __init__(self, boundaries: 'An array of LinearRings'=None, semantics: 'A semantic surface'=None):
        self._boundaries = []
        self._semantics = semantics
        if boundaries is not None:
            for ring in boundaries:
                if isinstance(ring, LinearRing):
                    self._boundaries.append(ring)
                else:
                    self._boundaries.append(LinearRing(ring))
    
    @property
    def boundaries(self):
        return self._boundaries
    
    @property
    def semantics(self):
        return self._semantics
    
    def has_holes(self):
        return len(self._boundaries) > 1

class LinearRing:
    """Describes a linear ring (i.e. a sequence of vertices)

    Mostly to be used as outer or inner ring of surfaces
    """

    def __init__(self, vertices=None):
        self._vertices = []
        if vertices is not None:
            if len(vertices) == 1:
                raise ValueError("A linear ring has to have more than one vertex")
            
            for v in vertices:
                if isinstance(v, Vertex):
                    self._vertices.append(v)
                else:
                    self.vertices.append(Vertex(v))
    
    @property
    def vertices(self):
        """Return the vertices of the ring"""
        return self._vertices

class Vertex:
    """
    Describes a zero dimensional object
    
    Has three float coordinates: x, y, z
    """

    def __init__(self, *args):
        """
        Parameters
        ----------
        There are 2 cases:

        1) one parameter (e.g. a list)
        2) three parameters: x, y, z : float
        """

        if len(args) == 1:
            self._coord = list(args[0])
        elif len(args) == 3:
            self._coord = list(args)
        else:
            raise ValueError("Cannot initialise such a vertex")
    
    @property
    def x(self):
        """Return the x coordinate"""
        return self._coord[0]
    
    @property
    def y(self):
        """Return the y coordinate"""
        return self._coord[1]

    @property
    def z(self):
        """Return the z coordinate"""
        return self._coord[2]
    
    def __eq__(self, other):
        return self._coord == other._coord
    
    def __add__(self, other):
        return Vertex(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vertex(self.x - other.x, self.y - other.y, self.z - other.z)

def vertices_from_tuple(coords: Tuple[Tuple[float, float, float]]) -> List[Vertex]:
    return [Vertex(c[0], c[1], c[2]) for c in coords]