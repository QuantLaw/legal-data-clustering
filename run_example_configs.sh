#!/bin/bash

# Complexity paper
python . de preprocess cluster cluster_evolution_graph --number-of-modules 100 --consensus 1000
python . us preprocess cluster cluster_evolution_graph --number-of-modules 100 --consensus 1000

# Thesis

# Vergleich der Algorithmen
python . de preprocess cluster --clustering-method louvain infomap --seed 1 --snapshot 2018-01-01
python . us preprocess cluster --clustering-method louvain infomap --seed 1 --snapshot 2018

# Verlgeich der Modelle
python . de preprocess cluster --clustering-method louvain --seed 1 --pp-co-occurrence -1 -2 --pp-co-occurrence-type paragraph --snapshot 2018-01-01 --markov-time 1 0.7 0.5

# Verlgeich des Detailgrads
python . de preprocess cluster --clustering-method louvain --seed 1 --pp-ratio 5 --pp-merge 0 --pp-co-occurrence -2 --pp-co-occurrence-type paragraph --snapshot 2018-01-01 --markov-time 1

# Zeitlich mittel
python . de preprocess cluster cluster_evolution_graph --clustering-method louvain --consensus 1000  --pp-co-occurrence -2 --pp-co-occurrence-type paragraph --markov-time 0.5

# Zeitlich grob
python . de preprocess cluster cluster_evolution_graph --clustering-method louvain --seed 1 --pp-co-occurrence -2 --pp-co-occurrence-type paragraph --consensus 1000
