import taichi as ti
from vector import *
import ray
from material import Material, empty_material


# struct for hittable records
HitRecord = ti.types.struct(p=Point, normal=Vector, t=ti.f32, front_face=ti.i32)

@ti.func
def empty_hit_record():
    ''' Constructs an empty hit record'''
    return HitRecord(p=Point(0.0), normal=Vector(0.0), t=0.0, front_face=1)


@ti.func
def set_face_normal(r, outward_normal, rec: ti.template()):
    ''' pass in hit record by reference and set front face and normal '''
    rec.front_face = r.dir.dot(outward_normal) < 0.0
    rec.normal = outward_normal if rec.front_face == 1 else -outward_normal


# struct for sphere
Sphere = ti.types.struct(center=Point, radius=ti.f32, material=Material)


def create_sphere(center, radius, material):
    return Sphere(center=center, radius=radius, material=material)

@ti.func
def hit_sphere(sphere, r, t_min, t_max):
        ''' Intersect a ray with a given center and radius.
            Note we pass in the hit record by reference. '''
        hit = False
        rec = empty_hit_record()

        oc = r.orig - sphere.center
        a = r.dir.norm_sqr()
        half_b = oc.dot(r.dir)
        c = oc.norm_sqr() - sphere.radius ** 2

        discriminant = half_b ** 2 - a * c
        # check hit only if discriminint is > 0
        if discriminant >= 0.0:
            sqrtd = ti.sqrt(discriminant)
            root = (-half_b - sqrtd) / a
            hit = (root >= t_min and root < t_max)
            if not hit:
                root = (-half_b + sqrtd) / a
                hit = (root >= t_min and root < t_max)

            if hit:
                rec.t = root
                rec.p = ray.at(r, rec.t)
                outward_normal = (rec.p - sphere.center) / sphere.radius
                set_face_normal(r, outward_normal, rec)

        return hit, rec


@ti.data_oriented
class HittableList:
    def __init__(self):
        self.objects = []

    def add(self, object):
        self.objects.append(object)

    def commit(self):
        ''' Save the sphere data and material info so we can loop over these.'''
        self.n = len(self.objects)
        self.spheres = Sphere.field(shape=(self.n,))

        for i, sphere in enumerate(self.objects):
            self.spheres[i] = sphere

    @ti.func
    def hit(self, r, t_min, t_max):
        hit_anything = False
        closest_so_far = t_max
        rec = empty_hit_record()
        mat_info = empty_material()

        for i in range(self.n):
            hit, temp_rec = hit_sphere(self.spheres[i], r, t_min, closest_so_far)
            if hit:
                hit_anything = True
                closest_so_far = temp_rec.t
                rec = temp_rec
                # we return the material info not the material because
                # taichi doesn't yet deal with assigning object pointers
                mat_info = self.spheres[i].material

        return hit_anything, rec, mat_info
