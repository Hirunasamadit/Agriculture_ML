import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def combined_features(row):
    return row['productName'] + " " + row['description'] + " " + row['productCatrgoryName']


def find_similar(product_id, df, num_of_products=5):
    features = ['productName', 'description', 'productCatrgoryName']
    for feature in features:
        df[feature] = df[feature].fillna('')

    df["combined_features"] = df.apply(combined_features, axis=1)

    cv = CountVectorizer()
    count_matrix = cv.fit_transform(df["combined_features"])

    cosine_sim = cosine_similarity(count_matrix)

    product_index = df[df._id_x == product_id]["index"].values[0]

    similar_products = list(enumerate(cosine_sim[product_index]))

    sorted_similar_products = sorted(similar_products, key=lambda x: x[1], reverse=True)

    i = 0
    id_list = []
    for product in sorted_similar_products:
        id_list.append(df[df.index == product[0]]["_id_x"].values[0])
        i = i + 1
        if i > num_of_products:
            break

    print(id_list)

    return id_list


def find_similar_products(product_id, num_of_products=5):
    df = pd.read_csv(r"data/processed.csv")

    # if product_id is in the database
    if df[df._id_x == product_id].empty:
        # get 5 random product _id_x
        print("Product not found in database. Here are 5 random products")
        random_products = df.sample(n=num_of_products)
        print(random_products["_id_x"].values)

        return random_products["_id_x"].values
    else:
        return find_similar(product_id, df, num_of_products)

product = "644a7bd507fc722cd1139862"
find_similar_products(product)
