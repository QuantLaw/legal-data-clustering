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
python . de preprocess cluster cluster_evolution_mappings cluster_evolution_graph cluster_inspection cluster_evolution_inspection --clustering-method louvain --consensus 1000  --pp-co-occurrence -2 --pp-co-occurrence-type paragraph --markov-time 1 0.5

# Source graph form Steuerrecht zoom in
python . de preprocess --pp-co-occurrence 0 -1 -2 --pp-co-occurrence-type paragraph --pp-merge 0 --pp-ratio 1 --pp-decay 1 --snapshot 2018-01-01


# Complexity paper

echo "Thesis done"

python . de preprocess cluster cluster_evolution_mappings cluster_evolution_graph cluster_inspection cluster_evolution_inspection --number-of-modules 100 --consensus 1000 --clustering-method infomap infomap-directed
python . us preprocess cluster cluster_evolution_mappings cluster_evolution_graph cluster_inspection cluster_evolution_inspection --number-of-modules 100 --consensus 1000 --clustering-method infomap infomap-directed

echo "Main paper done"

# Stability analysis
python . us preprocess cluster cluster_evolution_mappings cluster_evolution_graph cluster_inspection cluster_evolution_inspection --number-of-modules $(python -c "print(*[x for x in range(0, 150+1, 10)])") 200 --consensus 1000 --clustering-method infomap
python . de preprocess cluster cluster_evolution_mappings cluster_evolution_graph cluster_inspection cluster_evolution_inspection --number-of-modules $(python -c "print(*[x for x in range(0, 150+1, 10)])") 200 --consensus 1000 --clustering-method infomap

echo "Stability undirected done"

# Stability analysis
python . us preprocess cluster cluster_evolution_mappings cluster_evolution_graph cluster_inspection cluster_evolution_inspection --number-of-modules $(python -c "print(*[x for x in range(0, 150+1, 10)])") 200 --consensus 1000 --clustering-method infomap infomap-directed
python . de preprocess cluster cluster_evolution_mappings cluster_evolution_graph cluster_inspection cluster_evolution_inspection --number-of-modules $(python -c "print(*[x for x in range(0, 150+1, 10)])") 200 --consensus 1000 --clustering-method infomap infomap-directed
