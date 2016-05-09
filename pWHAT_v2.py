from __future__ import division
import os, sys, math
import matplotlib.pyplot as plt
import numpy as np
import decimal
decimal.setcontext(decimal.Context(prec=34))


class data_item():
    def __init__(self, id, decisions, objective):
        self.id = id
        self.decisions = decisions
        self.objective = objective

    def __repr__(self):
        return str(self.id)+ "|" +",".join(map(str, self.decisions)) + "|" + str(self.objective)


def euclidean_distance(list1, list2):
    assert(len(list1) == len(list2)), "The points don't have the same dimension"
    distance = sum([(i - j) ** 2 for i, j in zip(list1, list2)]) ** 0.5
    assert(distance >= 0), "Distance can't be less than 0"
    return distance


def similarity(list1, list2):
    """higher score indicates they are very different"""
    same = 0
    diff = 0
    for a, b in zip(list1, list2):
        if a != b: diff += 1
        else: same += 1
    number1 = int("".join(map(str, list1)))
    number2 = int("".join(map(str, list2)))
    return math.exp(diff)/(math.exp(same) * (number1 - number2))


def diff(a, b):
    b = set(b)
    return [aa for aa in a if aa not in b]


def furthest(one, all_members):
        """Find the distant point (from the population) from one (point)"""
        ret = None
        ret_distance = -1 * 1e10
        for member in all_members:
            if equal_list(one, member) is True:
                continue
            else:
                temp = euclidean_distance(one, member)
                if temp > ret_distance:
                    ret = member
                    ret_distance = temp
        return ret


def equal_list(lista, listb):
        """Checks whether two list are same"""
        assert (len(lista) == len(listb)), "Not a valid comparison"
        for i, j in zip(lista, listb):
            if i == j:
                pass
            else:
                return False
        return True


def comparision_2n(data):
    from random import choice
    any_point = choice(data)
    east = furthest(any_point, data)
    west = furthest(east, data)
    return east, west


def comparision_n2(data):
    distance_matrix = [[-1 for _ in xrange(len(data))] for _ in xrange(len(data))]
    max_value = -1e10
    max_i = -1
    max_j = -1
    for i in xrange(len(data)):
        for j in xrange(1, len(data)):
            if i == j: distance_matrix[i][j] = 0
            elif distance_matrix[i][j] == -1:
                distance_matrix[i][j] = euclidean_distance(data[i], data[j])
                if distance_matrix[i][j] > max_value:
                    max_value = distance_matrix[i][j]
                    max_i = i
                    max_j = j
    return data[max_i], data[max_j]


def generate_hist(data):
    members = sorted(set([d.hotspot_scores for d in data]), reverse=True)
    d = {}
    for member in members:
        d[str(member)] = [dd.id for i, dd in enumerate(data) if dd.hotspot_scores == member]
    return d


def get_indices(data, count_members):
    indices_dict = generate_hist(data)
    return_indices = []
    for key in sorted(indices_dict.keys(), reverse=True):
        length_next = len(indices_dict[key])
        if len(return_indices) + length_next <= count_members: return_indices.extend(indices_dict[key])
        else:
            delta = count_members - len(return_indices)
            assert(delta < len(indices_dict[key])), "somethign is wrong"
            from random import shuffle
            shuffle(indices_dict[key])
            delta_e = indices_dict[key][:delta]
            return_indices.extend(delta_e)
            break

    assert(len(return_indices) == count_members), "Somethign is wrong"

    return return_indices


def find_hotspot(data, count_members):

    return get_indices(data, count_members)


def read_csv(filename, header=False):
    def transform(filename):
        return "./Data/input/" + filename

    import csv
    data = []
    f = open(transform(filename), 'rb')
    reader = csv.reader(f)
    for i,row in enumerate(reader):
        if i == 0 and header is False: continue  # Header
        elif i ==0 and header is True:
            H = row
            continue
        data.append(data_item(i, [1 if x == "1" else 0 for x in row[:-1]], float(row[-1]) * (10**4))) # TODO: DecisionTree regressor returns int values. As a work around I multiply all the class values by 10**4
    f.close()
    if header is True: return H, data
    return data


def add_spectral_dimensions(data):

    def x_form(a,b,c): return (a**2 + c**2 - b**2)/(2*c)

    def y_form(a, xx):
        if a - xx < 1e-6: return 0
        return (a**2 - xx**2)**0.5

    just_decisions = [d.decisions for d in data]

    east, west = comparision_2n(just_decisions)
    c = euclidean_distance(east, west)

    for d in data:
        a = euclidean_distance(east, d.decisions)
        b = euclidean_distance(west, d.decisions)
        x = x_form(a,b,c)
        y = y_form(a, x)
        d.spectral_decisions = [x, y]

    return data


def get_hotspot_scores(data):
    distance_matrix = [[-1 for _ in xrange(len(data))] for _ in xrange(len(data))]
    from sklearn.metrics import jaccard_similarity_score
    for i in xrange(len(data)):
        for j in xrange(i, len(data)):
            if distance_matrix[i][j] == -1 and i != j:
                # print data[i].spectral_decisions, data[j].spectral_decisions
                # print data[i].decisions, data[j].decisions
                distance_matrix[i][j] = euclidean_distance(data[i].spectral_decisions, data[j].spectral_decisions)
                distance_matrix[j][i] = distance_matrix[i][j]
            elif distance_matrix[i][j] == -1 and i == j:
                distance_matrix[j][i] = 0
            else:
                pass

    hotspot_scores = []
    for i in xrange(len(data)):
        data[i].hotspot_scores = sum([1/(distance_matrix[i][j]**0.5) for j in xrange(len(distance_matrix)) if distance_matrix[i][j] != 0])

    # [sum([1/data[i][j] for j in xrange(len(data))]) for i in xrange(len(data))]
    # print "Done calculating hotspot scores"
    return sorted(data, key=lambda x: x.hotspot_scores, reverse=True)


def WHEREDataTransformation(filename):
    from Utilities.WHERE.where import where
    # The Data has to be access using this attribute table._rows.cells
    import pandas as pd
    df = pd.read_csv(filename)
    headers = [h for h in df.columns if '$<' not in h]
    data = df[headers]
    clusters = where(data)

    return clusters


def sorting_function(list_data):
    hotspot_scores = [ld.hotspot_scores for ld in list_data]
    from numpy import percentile
    return percentile(hotspot_scores, 75) - percentile(hotspot_scores, 25)


def return_content(header, content):
    return_c = ",".join(header) + "\n"
    for c in content:
        return_c += ",".join(map(str, c.decisions)) + "," + str(c.objective) + "\n"

    return return_c


def list_compare(list1, list2):
    "returns true or false: http://stackoverflow.com/questions/9623114/check-if-two-unordered-lists-are-equal"
    import collections
    compare = lambda x, y: collections.Counter(x) == collections.Counter(y)
    return compare(list1, list2)


def run_experiment(dataset_name):
    # read raw data
    H, raw_data = read_csv(dataset_name, header=True)
    from random import shuffle
    indexes = range(len(raw_data))
    shuffle(indexes)
    # getting the reserve testing data
    training_reservior_indexes = indexes[:int(len(raw_data) * 0.4)]
    testing_indexes = indexes[int(len(raw_data) * 0.4):]

    training_data_reservior = [raw_data[i] for i in training_reservior_indexes]
    testing_data_reservior = [raw_data[i] for i in testing_indexes]

    # writing the training data into a file to start WHEREing
    content = return_content(H, training_data_reservior)
    temp_filename = "./temp_where.csv"
    f = open(temp_filename, "w")
    f.write(content)
    f.close()
    from os import system

    clusters = WHEREDataTransformation(temp_filename)
    clusters_data = {}
    for i, cluster in enumerate(clusters):
        for c in cluster:
            key = "[" + ",".join(map(str, c)) + "]"
            clusters_data[key] = i

    new_clusters = []
    for cluster in clusters:
        new_clusters.append([str(c) for c in cluster])

    raw_data = read_csv(dataset_name)
    spectral_data = add_spectral_dimensions(raw_data)
    data_dict = {}
    for d in spectral_data:
        key = "[" + ",".join(map(str, d.decisions)) + "]"
        data_dict[key] = d

    extracted_clusters = []
    for i, cluster in enumerate(clusters):
        temp = []
        for element in cluster:
            key = "[" + ",".join(str(element)[1:-1].split()) + "]"
            temp.append(data_dict[str(key)])
        extracted_clusters.append(temp)

    hotscores_extracted_clusters = []
    for ec in extracted_clusters: hotscores_extracted_clusters.append(get_hotspot_scores(ec))

    # for cluster ranking
    sorted_extracted_clusters = sorted(hotscores_extracted_clusters, key=lambda x: sorting_function(x))
    number_of_clusters = len(sorted_extracted_clusters)



    # getting testing reservior
    system("rm -f ./temp_where.csv")
    testing_content = return_content(H, testing_data_reservior)
    testing_temp_filename = "./temp_where.csv"
    f = open(temp_filename, "w")
    f.write(testing_content)
    f.close()

    testing_clusters =  WHEREDataTransformation(testing_temp_filename)
    testing_reserve = []
    for test_c in testing_clusters:
        from random import choice
        point = choice(test_c)
        for test_data_point in testing_data_reservior:
            if list_compare(point, test_data_point.decisions) is True:
                testing_reserve.append(test_data_point)
                testing_data_reservior.remove(test_data_point)
                break

    assert(len(testing_reserve) + len(testing_data_reservior) + len(training_data_reservior) == len(raw_data)), "something is wrong"

    fault_rate = 1
    count = 10
    training_indep = []
    training_dep = []
    while fault_rate > 0.07 and count < len(training_data_reservior)-1:
        training_indep = [sorted_extracted_clusters[c%number_of_clusters][int(c/number_of_clusters)].decisions for c in xrange(count) if c/number_of_clusters < len(sorted_extracted_clusters[c%number_of_clusters])]
        training_dep = [sorted_extracted_clusters[c%number_of_clusters][int(c/number_of_clusters)].objective for c in xrange(count) if c/number_of_clusters < len(sorted_extracted_clusters[c%number_of_clusters])]

        # assert(len(training_indep) == count), "something is wrong"
        # assert(len(training_dep) == count), "something is wrong"

        indep_testing_set = [td.decisions for td in testing_reserve]
        dep_testing_set = [td.objective for td in testing_reserve]

        from sklearn import tree
        CART = tree.DecisionTreeRegressor()
        CART = CART.fit(training_indep, training_dep)

        predictions = [float(x) for x in CART.predict(indep_testing_set)]
        mre = []
        for i, j in zip(dep_testing_set, predictions):
            mre.append(abs(i - j) / float(i))

        from numpy import mean
        fault_rate = mean(mre)
        if int(len(training_reservior_indexes)*0.01) != 0:
            count += int(len(training_reservior_indexes)*0.01)
        else:
            count += 1
        # print len(training_indep), sum([len(s) for s in sorted_extracted_clusters]), len(testing_reserve), len(testing_data_reservior)

    assert(len(training_indep)==len(training_dep)), "Something is wrong"
    from sklearn import tree
    CART = tree.DecisionTreeRegressor()
    CART = CART.fit(training_indep, training_dep)

    indep_testing_set = [td.decisions for td in testing_data_reservior]
    dep_testing_set = [td.objective for td in testing_data_reservior]

    predictions = [float(x) for x in CART.predict(indep_testing_set)]
    mre = []
    for i, j in zip(dep_testing_set, predictions):
        mre.append(abs(i - j) / float(i))

    from numpy import mean
    return mean(mre), len(training_dep)

if __name__ == "__main__":
    import sys
    from random import seed
    seed(10)
    # datasets = [    "AJStats.csv", "Apache.csv", "BerkeleyC.csv", "BerkeleyDB.csv", "BerkeleyDBC.csv", "BerkeleyDBJ.csv",
    #                 "clasp.csv", "Dune.csv", "EPL.csv", "Hipacc.csv", "JavaGC.csv", "LinkedList.csv",
    #                 "lrzip.csv", "PKJab.csv", "SQLite.csv", "Wget.csv", "x264.csv", "ZipMe.csv"]

    datasets = ["x264.csv", "ZipMe.csv"]
    for dataset in datasets:
        mean_mre = []
        mean_length = []
        for _ in xrange(10):
            print ".",
            sys.stdout.flush()
            mre, datalength = run_experiment(dataset)
            mean_mre.append(mre)
            mean_length.append(datalength)
        from numpy import mean, std
        print
        print dataset, round(mean(mean_mre)*100, 3), round(std(mean_mre)*100, 3), round(mean(mean_length), 3), round(std(mean_length), 3)
        print [round(r * 100, 3) for r in mean_mre]
        print [round(r, 3) for r in mean_length]
        print
