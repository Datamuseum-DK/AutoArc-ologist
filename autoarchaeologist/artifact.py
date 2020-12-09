#!/usr/bin/env python3

'''
    AutoArchaeologist Artifact Class
    --------------------------------

    `ArtifactClass` is hidden by the function `Artifact` which
    ensures their uniqueness.
'''

import hashlib

import autoarchaeologist.excavation as excavation
import autoarchaeologist.generic.hexdump as hexdump
import autoarchaeologist.record as record
import autoarchaeologist.scattergather as scattergather

class DuplicateName(Exception):
    ''' Set names must be unique '''

class ArtifactClass():

    '''
        Artifact[Class]
        ---------------

        Artifacts are just bytearrays with a high-school diploma.

        Artifacts are always created relative to another artifact,
        or in the case of the top-level artifacts, relative to the
        excavation, which duck-types as an Artifact to make this work.

        Artifacts are somehow derived from their parent, typical
        examples being sections, like the first half of a paper-tape,
        subsets, like the concatenation of a file's blocks in from
        a filesystem or transformations like uncompression.

        XXX

    '''

    def __init__(self, up, digest, bits):
        assert len(bits) > 0
        if isinstance(bits, (memoryview, scattergather.ScatterGather)):
            self.bdx = bits
        else:
            self.bdx = memoryview(bits)

        self.digest = digest

        self.parents = []
        self.children = []

        self.named = None
        self.interpretations = []
        self.notes = set()
        self.types = set()
        self.descriptions = []
        self.comments = []
        self.taken = False
        self.layout = []

        self.add_parent(up)
        self.top = up.top
        self.top.add_artifact(self)

        self.index_representation = None
        self.link_to = ""

        self.by_class = {} # Experimental extension point

    def __str__(self):
        return "{A %d %s}" % (len(self), self.name())

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self.bdx)

    def __hash__(self):
        return int(self.digest[:8], 16)

    def __getitem__(self, idx):
        return self.bdx[idx]

    def __lt__(self, other):
        if isinstance(other, excavation.Excavation):
            return 1
        return self.name() < other.name()

    def __iter__(self):
        yield from self.bdx

    def iterrecords(self):
        if isinstance(self.bdx, scattergather.ScatterGather):
            yield from self.bdx.iterrecords()
        else:
            yield self.bdx

    def tobytes(self):
        return self.bdx.tobytes()

    def writetofile(self, fd):
        if isinstance(self.bdx, scattergather.ScatterGather):
            self.bdx.writetofile(fd)
        else:
            fd.write(self.bdx)

    def name(self):
        ''' Get the canonical name of the artifact '''
        if self.named:
            return "\u27e6" + self.named + "\u27e7"
        return "\u27e6" + self.digest[:self.top.digest_prefix] + "\u27e7"

    def add_parent(self, parent):
        ''' Attach to parent, and vice-versa '''
        assert self != parent
        self.parents.append(parent)
        parent.children.append(self)

    def set_name(self, name, fallback=True):
        ''' Set a unique name '''
        if self.named == name:
            return
        if self.named is not None:
            if fallback:
                self.add_note(name)
                self.top.add_to_index(name, self)
                return
            raise DuplicateName("Name clash '%s' vs '%s'" % (self.named, name))
        if name in self.top.names:
            if fallback:
                self.add_note(name)
                self.top.add_to_index(name, self)
                return
            raise DuplicateName("Name already used '%s'" % name)
        self.top.names.add(name)
        self.named = name
        self.top.add_to_index(name, self)

    def add_type(self, typ):
        ''' Add type designation (also as note) '''
        self.types.add(typ)
        self.top.add_to_index(typ, self)

    def has_type(self, note):
        ''' Check if not already exists '''
        return note in self.types

    def add_interpretation(self, owner, func):
        ''' Add an interpretation '''
        self.interpretations.append((owner, func))

    def add_description(self, desc):
        ''' Add a description '''
        self.descriptions.append(desc)

    def add_comment(self, desc):
        ''' Add a comment '''
        self.comments.append(desc)
        self.notes.add("Has Comment")

    def add_note(self, note):
        ''' Add a note '''
        self.notes.add(note)
        self.top.add_to_index(note, self)

    def has_note(self, note):
        ''' Check if not already exists '''
        return note in self.notes

    def iter_types(self, recursive=False):
        ''' Return all notes that apply to this artifact '''
        yield from self.types
        if recursive:
            for child in self.children:
                assert child != self, (child, self)
                yield from child.iter_types(recursive)

    def iter_notes(self, recursive=False):
        ''' Return all notes that apply to this artifact '''
        yield from [(self, i) for i in self.notes]
        if recursive:
            for child in self.children:
                assert child != self, (child, self)
                yield from child.iter_notes(recursive)

    def record(self, layout, **kwargs):
        ''' Extract a compound record '''
        return record.Extract_Record(self, layout, **kwargs)

    def filename_for(self, *args, **kwargs):
        ''' ask excavation '''
        return self.top.filename_for(self, *args, **kwargs)

    def create(self, bits=None, start=None, stop=None, records=None):
        ''' Return a new or old artifact for some bits '''
        if records:
            assert bits is None
            assert len(records) > 0
            bits = scattergather.ScatterGather(records)
            digest = bits.sha256()
        elif isinstance(bits, memoryview):
            digest = hashlib.sha256(bits.tobytes()).hexdigest()
        elif bits:
            digest = hashlib.sha256(bits).hexdigest()
        else:
            assert stop > start
            assert stop <= len(self)
            if not start and stop == len(self):
                return self
            bits = self[start:stop]
            digest = hashlib.sha256(bits.tobytes()).hexdigest()
        this = self.top.hashes.get(digest)
        if not this:
            this = ArtifactClass(self, digest, bits)
        else:
            this.add_parent(self)
        if start or stop:
            self.layout.append((start, stop, this))
        return this

    def examined(self):
        ''' Examination of this artifact is complete '''
        # XXX: create left over slices
        l = []
        offset = 0
        for start, stop, src in sorted(self.layout):
            if start is None or stop is None:
                continue
            if offset < start:
                l.append((offset, start))
            offset = stop
        if not offset:
            return
        if offset != len(self):
            l.append((offset, len(self)))
        for start, stop in l:
            self.create(start=start, stop=stop)

    def summary(self, link=True, ident=True, notes=False):
        ''' Produce a one-line summary '''
        if not link or not ident or not self.index_representation:
            txt = []
            nam = ""
            if ident:
                if link:
                    nam = self.top.html_link_to(self) + " "
                else:
                    nam = self.name() + " "
            j = set()
            for i in self.iter_types(True):
                if i not in j:
                    txt.append(i)
                    j.add(i)
            if self.descriptions:
                txt += sorted(self.descriptions)
            if notes:
                nn = sorted({y for _x, y in self.iter_notes(True)})
                txt += nn[:35]
                if len(nn) > 35:
                    txt.append("…")
            if not link or not ident:
                return nam + ", ".join(txt)
            self.index_representation = nam + ", ".join(txt)
        return self.index_representation

    def html_page(self, fo):
        ''' Produce HTML page '''
        fo.write("<H2>" + self.summary(link=False) + "</H2>\n")
        fo.write("<pre>\n")
        fo.write("    Length: %d (0x%x)\n" % (len(self), len(self)))
        for i in self.descriptions:
            fo.write("    Description: " + i + "\n")
        if self.types:
            fo.write("    Types: " + ", ".join(sorted(self.types)) + "\n")
        if self.notes:
            fo.write("    Notes: " + ", ".join(sorted({y for x, y in self.iter_notes(True)}))+ "\n")
        fo.write("</pre>\n")

        fo.write("<H4>Derivation</H4>\n")
        fo.write("<pre>\n")
        self.html_derivation(fo)
        fo.write("</pre>\n")

        if self.children and not self.interpretations:
            self.html_interpretation_children(fo, self)

        if self.comments:
            fo.write("<H4>NB: Comments at End</H4>\n")

        if self.interpretations:
            for _owner, func in self.interpretations:
                func(fo, self)
        else:
            self.html_interpretation_hexdump(fo, self)

        if self.comments:
            fo.write("<H4>Comments</H4>\n")
            fo.write("<pre>\n")
            for i in self.comments:
                fo.write(i + "\n")
            fo.write("</pre>\n")

    def html_interpretation_children(self, fo, _this):
        ''' Default interpretation list of children'''

        fo.write("<H4>Children</H4>\n")
        fo.write("<pre>\n")
        for start, stop, this in sorted(self.layout):
            fo.write("  0x%08x" % start + "-0x%08x  " % stop)
            fo.write(this.summary() + "\n")
        fo.write("</pre>\n")

    def html_interpretation_hexdump(self, fo, _this):
        ''' Default interpretation as hexdump '''
        fo.write("<H4>HexDump</H4>\n")
        fo.write("<pre>\n")

        if not isinstance(self.bdx, scattergather.ScatterGather):
            if len(self) > self.top.hexdump_limit:
                hexdump.hexdump_to_file(
                    self[:self.top.hexdump_limit].tobytes(),
                    fo
                )
                fo.write("[…]\n")
            else:
                hexdump.hexdump_to_file(self.tobytes(), fo)
        else:
            done = 0
            idx = 0
            for n, r in enumerate(self.iterrecords()):
                fo.write("Record #0x%x\n" % n)
                hexdump.hexdump_to_file(r.tobytes(), fo)
                fo.write("\n")
                done += len(r)
                if done > self.top.hexdump_limit:
                    break

    def html_derivation(self, fo):
        ''' Recursively document how this artifact came to be '''
        prefix = ""
        for p in sorted(self.parents):
            t = p.html_derivation(fo)
            if len(t) > len(prefix):
                prefix = t
            fo.write(t + "└─" + self.summary() + '\n')
        return prefix + "    "

    def html_interpretation_sliced(self, fo, this):
        ''' Produce table of slicings '''
        # XXX: slices may overlap
        assert this == self
        fo.write("<H3>Sliced</H3>\n")
        fo.write("<pre>\n")
        for sln in self.slicings:
            for slab in sorted(sln):
                fo.write("0x%05x-0x%05x " % (slab.offset, slab.offset + len(slab.this)))
                fo.write(slab.this.summary(notes=True) + "\n")
            fo.write("\n")
        fo.write("</pre>\n")
