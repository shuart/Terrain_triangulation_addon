# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    'name': 'Terrain Generator',
    'author': 'Stephane Huart',
    'version': (0, 7, 0),
    "blender": (2, 6, 5),
    'location': 'View3D > Ctrl-C',
    'description': 'Generate terrain from point cloud',
    "warning": "some corner cases",
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/'
                '',
    'tracker_url': '',
    'category': '3D View'}

import bpy
import math
import mathutils
import time
import bmesh


def dewall_triangulation(source_mesh,node_part_list,equ_list):

    face_done=0 #init variables
    lastreport=0
    tessedges=[]
    tessedgessign=[]
    nodedistance=[]
    me = source_mesh
    bm = bmesh.new()   # create an empty BMesh
    bm.from_mesh(me)   # fill it in from a Mesh

    node1=0 #create first triangle
    node1loc=node_part_list[0]
    
    lenght=1000000000000000 #finde nearest vertex
    node2=1 #initialise node 2
    iter=0
    for v in node_part_list: #parcoure les noeuds originaux
        if v != node_part_list[node1]:
            cand_loc=v
            cand_len=find_length(node1loc,cand_loc)
            if lenght > cand_len:
                node2=iter
                lenght=cand_len
        iter=iter+1

    #get node 3
    #1-construc circle
    iter=0
    nin=True
    while nin == True:
        v = node_part_list[iter]
        if v != node_part_list[node1] and v != node_part_list[node2]:
            node3=iter
            circle=get_circle(node1,node2,node3,node_part_list)
            #then check if other nodes are in
            nin=False
            for vi in node_part_list:
                if vi != node_part_list[node1] and vi != node_part_list[node2]and vi != node_part_list[node3]:
                    cand_loc=vi
                    cand_len=find_length(circle,cand_loc)
                    if cand_len < circle[2]:
                        nin=True
        iter=iter+1

    #create face

    v1 = bm.verts[equ_list[node1]]
    v2 = bm.verts[equ_list[node2]]
    v3 = bm.verts[equ_list[node3]]

    bm.faces.new([v1, v2, v3])

    tessedges.append([node1,node2])
    tessedges.append([node2,node3])
    tessedges.append([node3,node1])
    tessedgessign.append(node3)
    tessedgessign.append(node1)
    tessedgessign.append(node2)

    #do it for other faces
    while (len( tessedges)) !=0 :
         node1 =tessedges[0][0]
         node2 =tessedges[0][1]
         test=tessedgessign[0]
         del tessedges[0]
         del tessedgessign[0]
         
         #check wich vert is on good side

         affnodes=[]
         nodedistance=[]
         x1=node_part_list[node1][0]
         x2=node_part_list[node2][0]
         x3=node_part_list[test][0]
         y1=node_part_list[node1][1]
         y2=node_part_list[node2][1]
         y3=node_part_list[test][1]
         vect1=mathutils.Vector((x2-x1, y2-y1,0))
         vect2=mathutils.Vector((x3-x1, y3-y1,0))
         testres=vect1.cross(vect2)
         iter=0
         for t in node_part_list:
             x4=t[0]
             y4=t[1]
             vect3=mathutils.Vector((x4-x1, y4-y1,0))
             candres=vect3.cross(vect1)
             if (candres*testres)>0:
                 affnodes.append(iter)
                 #calculate distance from node1 for ordering
                 coord_node1=node_part_list[node1]
                 coord_t=t
                 dist=find_length(coord_node1,coord_t)
                 nodedistance.append([iter,dist])

             iter=iter+1
#         print('les noeuds dispo pour cet edge  sont')
#         for a in affnodes:
#            print(a)
#            print(source_mesh.vertices[a].co)

         if (len( affnodes)) !=0:
             nodedistance.sort(key=lambda vert: vert[1])#sort aff vert by distance

             node3 =find_node3(node_part_list,node1,node2,affnodes,nodedistance)
             if node3 != False:

                 #create face
                 #TODO change to make mode switch only once
                 v1 = bm.verts[equ_list[node1]]
                 v2 = bm.verts[equ_list[node2]]
                 v3 = bm.verts[equ_list[node3]]

                 bm.faces.new([v1, v2, v3])

                 face_done=face_done+1
                 report=face_done/(len(source_mesh.vertices)*2)*100
                 if report > lastreport+5:
                    print(report)
                    lastreport=report

                 if [node3,node2] in tessedges:
                     delindex=tessedges.index([node3,node2])
                     del tessedges[delindex]
                     del tessedgessign[delindex]
                 elif [node2,node3] in tessedges:
                     delindex=tessedges.index([node2,node3])
                     del tessedges[delindex]
                     del tessedgessign[delindex]
                 else:
                     #print('add an edge')
                     tessedges.append([node2,node3])
                     tessedgessign.append(node1)

                 if [node3,node1] in tessedges:
                     delindex=tessedges.index([node3,node1])
                     del tessedges[delindex]
                     del tessedgessign[delindex]
                 elif [node1,node3] in tessedges:
                     delindex=tessedges.index([node1,node3])
                     del tessedges[delindex]
                     del tessedgessign[delindex]
                 else:
                     #print('add an edge')
                     tessedges.append([node1,node3])
                     tessedgessign.append(node2)
    bm.to_mesh(me)
    bpy.context.area.tag_redraw()

#coords=[(-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0 ,-1.0), \
#(-1.0, 1.0,-1.0), (0.0, 0.0, 1.0)]
#
## Define the faces by index numbers. Each faces is defined by 4 consecutive integers.
## For triangles you need to repeat the first vertex also in the fourth position.
#faces=[ (2,1,0,3), (0,1,4,0), (1,2,4,1), (2,3,4,2), (3,0,4,3)]

def find_node3(node_part_list,node1,node2,affnodes,nodedistance):
    #check wich is the third node
    #get node 3
    #1-construc circle
    #print(node_part_list[0],source_mesh.vertices[0])
    iter=0
    nin=True
    sp=False
    last_circle_size=0
    while nin == True:

        if (len(affnodes))==iter:
            return False
        n_index=nodedistance[iter][0]
        v = node_part_list[n_index]

        if v != node_part_list[node1] and v != node_part_list[node2] and n_index in affnodes:
            node3=n_index
            circle=get_circle(node1,node2,node3,node_part_list)
            #then check if other nodes are in
            nin=False
            vinumber= -1
            if sp == False or circle[2] < last_circle_size:
#                print('test de sp ou cervle reussi')
                find_in = False
                while find_in == False and vinumber<(len(node_part_list)-1):
                    vinumber=vinumber+1
                    vi = node_part_list[vinumber]
                    if vi != node_part_list[node1] and vi != node_part_list[node2]and vi != node_part_list[node3]:

                        cand_loc=vi
                        cand_len=find_length(circle,cand_loc)
#                        print(cand_len)
                        if cand_len < circle[2]:
                            nin=True
                            sp=False
                            find=True
                            last_circle_size=circle[2]
            else:
                nin=True
                print('cercle rejete!')

        iter=iter+1

    return node3

def find_length(vloc,cand_loc):

    term1=(cand_loc[0]-vloc[0])
    term2=(cand_loc[1]-vloc[1])
    length=term1*term1+term2*term2

    return length

def get_circle(node1,node2,node3,node_part_list):
    #get slope
    ay=node_part_list[node1][1]
    by=node_part_list[node2][1]
    cy=node_part_list[node3][1]
    ax=node_part_list[node1][0]
    bx=node_part_list[node2][0]
    cx=node_part_list[node3][0]
    x1 = (bx + ax) / 2
    y1 = (by + ay) / 2
    dy1 = bx - ax
    dx1 = -(by - ay)

    x2 = (cx + bx) / 2
    y2 = (cy + by) / 2
    dy2 = cx - bx
    dx2 = -(cy - by)

    ox = (y1 * dx1 * dx2 + x2 * dx1 * dy2 - x1 * dy1 * dx2 - y2 * dx1 * dx2)/ (dx1 * dy2 - dy1 * dx2)

    if dx1 == 0:
        #oy=y1
        #ox = (oy - y2) * dx2/dy2 + x2
        oy = (ox - x2) * dy2 / dx2 + y2
    elif dx2 == 0:
        #oy=y2
        #ox = (oy - y1) * dx1/dy1 + x1
        oy = (ox - x1) * dy1 / dx1 + y1
    elif dy1 == 0:
        #ox=x1
        oy = (ox - x2) * dy2 / dx2 + y2
    elif dy2 == 0:
        #ox=x2
        oy = (ox - x1) * dy1 / dx1 + y1

    else:
        oy = (ox - x1) * dy1 / dx1 + y1

    dx = ox - ax
    dy = oy - ay
    radius2 = dx * dx + dy * dy


    cx=ox
    cy=oy
    circle=[cx,cy,radius2]
    return circle


def get_circle2(node1,node2,node3,source_mesh):
    #get slope
    print('!!!!!! can bug here')
    print(source_mesh.vertices[node1].co)
    print(source_mesh.vertices[node2].co)
    print(source_mesh.vertices[node3].co)
    y1=source_mesh.vertices[node1].co[1]
    y2=source_mesh.vertices[node2].co[1]
    y3=source_mesh.vertices[node3].co[1]
    x1=source_mesh.vertices[node1].co[0]
    x2=source_mesh.vertices[node2].co[0]
    x3=source_mesh.vertices[node3].co[0]
    ma=(y2-y1)/(x2-x1)
    mb=(y3-y2)/(x3-x2)
    cx=(ma*mb*(y3-y1)+ma*(x3+x2)-mb*(x1+x2))/2*(ma-mb)
    cy=-(1/mb)*(cx-(x2+x3)/2)+(y2+y3)/2
    print(cx)
    radius2=((cx-x1)*(cx-x1)+(cy-y1)*(cy-y1))
    circle=[cx,cy,radius2]
    return circle
    
    
class OBJECT_PT_Tgen(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Terrain generator"


    def draw_header(self, context):
        layout = self.layout
        layout.label(text="Tgen", icon="MOD_BUILD")

    def draw(self, context):

        scn = context.scene

        layout = self.layout
        row = layout.row()
        row.label(text="Generate terrain:")
        row = layout.row()
        row.operator("dewall_tri.", text="Using Dewall triangulation")


class OBJECT_OT_Tgen_dewall_tri(bpy.types.Operator):
    bl_label = "tgen_dewall_tri"
    bl_idname = "dewall_tri."
    bl_description = "dewall triangulation"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def invoke(self, context, event):
        import bpy
        import time

        chunk=False
        t0 = time.time()

        scn = bpy.context.scene

        source_ob=bpy.context.active_object
        node_part_list=[]
        equ_list=[]
        source_mesh=source_ob.data
        for i in range(len(source_mesh.vertices)):
            if chunk ==True:
                if source_mesh.vertices[i].co[0] < (-4):
                    node_part_list.append(source_mesh.vertices[i].co.copy())
                    equ_list.append(i)
            else:
                node_part_list.append(source_mesh.vertices[i].co.copy())
                equ_list.append(i)

        dewall_triangulation(source_mesh,node_part_list,equ_list)

        print ("Dewall triangulation completed in", time.time() - t0, "seconds wall time")
        return{"FINISHED"}		

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
