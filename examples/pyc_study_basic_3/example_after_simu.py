analyser = pyc.CAnalyser(study.system_model.bkd)

analyser.printFilteredSeq(100,
                          "sequences.xml",
                          "PySeq.xsl")

indic_fig = study.indic_px_line(facet_row="comp",
                                title="Diagramme des flux systèmes",
                                labels={"instant":"Temps"})

if not(indic_fig is None):
    indic_filename = \
        os.path.join(".", "indic_basic.html")
    indic_fig.write_html(indic_filename)
