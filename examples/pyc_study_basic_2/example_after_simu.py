import os

import Pycatshoo as pyc


def execute_hook(study):

    def getPath(filename):
        return os.path.join(study.working_dir, filename)

    def getResultPath(filename):
        return os.path.join(study.results_dir, filename)

    analyser = pyc.CAnalyser(study.system_model.bkd)

    analyser.printFilteredSeq(100,
                              getResultPath("sequences.xml"),
                              getResultPath("PySeq.xsl"))

    indic_fig = study.indic_px_line(facet_row="comp",
                                    title="Diagramme des flux systèmes",
                                    labels={"instant": "Temps"})

    if not (indic_fig is None):
        indic_filename = getResultPath("indic_basic.html")
        indic_fig.write_html(indic_filename)
