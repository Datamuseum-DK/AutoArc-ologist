#!/usr/bin/env python3

# NB: This docstring is also used as interpretation

'''
   EEDB "secret filesystem" - VPID 0256 - TAG 0x70
   ===============================================

   This is a very fundamental "filesystem" which is only mentioned
   one single place in all the documentation we have: the FE_HANDBOOK,
   pdf page 185.

   The directory is displayed with the ``VDIR *`` command at the
   ``EEDB:`` prompt.

   The "filesystem" is simply a mapping from filename to (vpid,
   segment).

   The various object managers state files live here, which is what
   that entry in the FE_HANDBOOK is about, but there also seems to
   be other "magic files" such as the product authentication codes,
   and some files which looks like crumbs from manual interventions at
   the ``EEDB:`` prompt.

   Some of the files are text files, which can be shown on the console
   with the ``TYPE_FILE`` command at the ``EEDB:`` prompt.

   Open ends
   ---------

   The discovered content is only a small fraction of the entire
   segment, and further discovery is warranted.

   Amongst the "debris" are StringArrays with the object managers'
   names with a ".pure" suffix.  These may be related to the
   ``Archive_On_Shutdown`` facility in ``package Operator`` documented
   on pdf page 6 of Guru_Course_3.

   Get the namespace to point to the actual segments.

   Does ``INSTRUCTIONS_SPEC`` and ``load_inst_spec.script_LOG`` reveal
   anything we did not already know ?

   This would also be a good place to stash the passwords.

'''

from ....base import bitview as bv
from ....base import namespace
from .common import Segment, SegHeap, PointerArray, StringArray, StringPointer

class X00(bv.Struct):
    def __init__(self, bvtree, lo):
        super().__init__(
            bvtree,
            lo,
            x00_000_n_=-161,
            x00_008_n_=bv.Pointer(X01),
            x00_010_n_=bv.Pointer(),
            x00_011_n_=bv.Pointer(),
            x00_012_n_=bv.Pointer(),
            x00_013_n_=bv.Pointer(),
            #x00_014_n_=bv.Pointer(),
            #x00_015_n_=bv.Pointer(),
            #x00_016_n_=bv.Pointer(),
            #x00_017_n_=bv.Pointer(),
            vertical=True,
        )

class X01(bv.Struct):
    def __init__(self, bvtree, lo):
        super().__init__(
            bvtree,
            lo,
            x98_049_n_=-205,
            x98_096_p_=bv.Pointer(X01),
            x98_097_p_=bv.Pointer(X01),
            x98_098_p_=bv.Pointer(X01),
            x98_099_p_=bv.Pointer(X01),
        )

class X02(bv.Struct):
    def __init__(self, bvtree, lo):
        super().__init__(
            bvtree,
            lo,
            x02_000_n_=-32,
            x02_001_n_=-32,
            more=True,
            vertical=True,
        )
        self.add_field(
            "ptrs",
            bv.Array(
                self.x02_001_n.val,
                bv.Pointer(X03),
                vertical=True,
                #elide={0,},
            )
        )
        self.done()

class X03(bv.Struct):
    def __init__(self, bvtree, lo):
        super().__init__(
            bvtree,
            lo,
            x98_000_n__=bv.Constant(32, 0),
            x98_010_n_=bv.Pointer(StringArray),
            x98_048_n_=bv.Pointer(X03),
        )

class X04(bv.Struct):
    def __init__(self, bvtree, lo):
        super().__init__(
            bvtree,
            lo,
            x99_000_n__=bv.Constant(32, 0),
            x99_010_n_=StringPointer,
            x99_046_n_=-1,
            x99_047_n_=-22,
            x99_048_n_=-10,
            x99_049_n__=bv.Constant(32, 0x80),
            x99_080_n_=bv.Pointer(X04),
        )
        print(self.x99_010_n.dst().txt)
        NameSpace(
            name=self.x99_010_n.dst().txt,
            parent=bvtree.namespace,
            priv = self,
        )

class NameSpace(namespace.NameSpace):
    ''' ... '''

    KIND = "EEDB filesystem"

    TABLE = (
        ("r", "flag"),
        ("r", "vpid"),
        ("r", "segment"),
        ("l", "name"),
        ("l", "artifact"),
    )

    def ns_render(self):
        meta = self.ns_priv
        return [
            meta.x99_046_n.val,
            meta.x99_048_n.val,
            hex(meta.x99_047_n.val),
        ] + super().ns_render()

class V0256T70(Segment):

    VPID = 256
    TAG = 0x70

    def spelunk(self):

        self.namespace = NameSpace(
            name = "",
            separator = "",
        )

        with self.this.add_utf8_interpretation("What we have figured out") as file:
            file.write(__doc__)


        self.seg_heap = SegHeap(self, 0).insert()

        self.x00 = X00(self, self.seg_heap.hi).insert()
        self.x02 = X02(self, self.x00.x00_011_n.val).insert()

        PointerArray(
            self,
            self.x00.x00_013_n.val,
            dimension=101,
            cls=X04,
            elide={0,},
        ).insert()

        self.this.add_interpretation(self, self.namespace.ns_html_plain)
        self.this.top.add_interpretation(self, self.html_interpretation)

    def html_interpretation(self, file, this):
        self.namespace.ns_html_plain(file, this)