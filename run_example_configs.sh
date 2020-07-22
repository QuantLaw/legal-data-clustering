#!/bin/bash

# Thesis

# Vergleich der Algorithmen
python . de preprocess cluster --clustering-method louvain infomap --seed 1 --snapshot 2018-01-01
python . us preprocess cluster --clustering-method louvain infomap --seed 1 --snapshot 2018

# Verlgeich der Modelle
python . de preprocess cluster --clustering-method louvain --seed 1 --pp-co-occurrence -1 -2 --pp-co-occurrence-type paragraph --snapshot 2018-01-01 --markov-time 1 0.7 0.5

# Verlgeich des Detailgrads
python . de preprocess cluster --clustering-method louvain --seed 1 --pp-ratio 5 --pp-merge 0 --pp-co-occurrence -2 --pp-co-occurrence-type paragraph --snapshot 2018-01-01 --markov-time 1

# Zeitlich mittel / grob
python . de preprocess cluster cluster_evolution_graph --clustering-method louvain --consensus 1000  --pp-co-occurrence -2 --pp-co-occurrence-type paragraph --markov-time 1 0.5

# Source graph form Steuerrecht zoom in
python . de preprocess --pp-co-occurrence 0 -1 -2 --pp-co-occurrence-type paragraph --pp-merge 0 --pp-ratio 1 --pp-decay 1 --snapshot 2018-01-01


# Complexity paper

echo "Thesis done"

python . de preprocess cluster cluster_evolution_graph --number-of-modules 100 --consensus 1000 --clustering-method infomap infomap-directed
python . us preprocess cluster cluster_evolution_graph --number-of-modules 100 --consensus 1000 --clustering-method infomap infomap-directed

# Temp
python . us preprocess cluster cluster_evolution_graph --number-of-modules $(python -c "print(*[x for x in range(0, 200, 50)])") --consensus 1000 --clustering-method infomap
python . de preprocess cluster cluster_evolution_graph --number-of-modules $(python -c "print(*[x for x in range(0, 200, 50)])") --consensus 1000 --clustering-method infomap

# Temp
python . us preprocess cluster cluster_evolution_graph --number-of-modules $(python -c "print(*[x for x in range(0, 200, 10)])") --consensus 1000 --clustering-method infomap
python . de preprocess cluster cluster_evolution_graph --number-of-modules $(python -c "print(*[x for x in range(0, 200, 10)])") --consensus 1000 --clustering-method infomap

# Stability analysis
python . us preprocess cluster cluster_evolution_graph --number-of-modules $(python -c "print(*[x for x in range(0, 200, 10)])" --consensus 1000 --clustering-method infomap infomap-directed
python . de preprocess cluster cluster_evolution_graph --number-of-modules $(python -c "print(*[x for x in range(0, 200, 10)])" --consensus 1000 --clustering-method infomap infomap-directed
