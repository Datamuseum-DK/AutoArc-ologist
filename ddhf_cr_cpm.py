'''
Christian Rovsing CR8 Artifacts from Datamuseum.dk's BitStore
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'''

from autoarchaeologist import ddhf

from autoarchaeologist.base import type_case

from autoarchaeologist.generic import samesame
from autoarchaeologist.generic import textfiles
from autoarchaeologist.DigitalResearch import cpm

class TxtFile(textfiles.TextFile):
    VERBOSE=False
    MAX_TAIL=2048

cpm.cpm_filename_typecase.set_slug(0x5f, '_', '_')

class CR8_Ds2089(type_case.DS2089):
    ''' ... '''

    def __init__(self):
        super().__init__()
        self.set_slug(0x0d, ' ', '')
        self.set_slug(0x1a, ' ', '«eof»', self.EOF)

        #self.set_slug(0x00, ' ', '«nul»', self.EOF)
        #self.set_slug(0x07, ' ', '«bel»')
        #self.set_slug(0x0c, ' ', '«ff»\n')
        #self.set_slug(0x0e, ' ', '«so»')
        #self.set_slug(0x0f, ' ', '«si»')
        #self.set_slug(0x19, ' ', '«eof»', self.EOF)
        #self.set_slug(0x7f, ' ', '')

class CR8TypeCase(type_case.Ascii):

    def __init__(self):
        super().__init__()
        self.set_slug(0x0d, ' ', '')
        self.set_slug(0x1a, ' ', '«eof»', self.EOF)

class CR_CPM(ddhf.DDHF_Excavation):

    ''' All CR8 artifacts '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.type_case = CR8_Ds2089()

        self.add_examiner(cpm.CpmFileSystem)
        self.add_examiner(TxtFile)
        self.add_examiner(samesame.SameSame)

        self.from_bitstore(
            "CR/CR7",
            "CR/CR8",
            "CR/CR16",
        )

if __name__ == "__main__":
    ddhf.main(
        CR_CPM,
        html_subdir="cr_cpm",
        ddhf_topic = 'Christian Rovsing CR7, CR8 & CR16 CP/M',
        ddhf_topic_link = 'https://datamuseum.dk/wiki/Christian_Rovsing_A/S'
    )