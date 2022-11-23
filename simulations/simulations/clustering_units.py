from typing import Any, Dict, Iterator, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler


def cluster_units(
    unit_vectors: Dict[str, Dict[str, Any]], n_clusters: int
) -> Iterator[Tuple[List[str], str]]:
    np.random.seed(42)
    df = pd.DataFrame(
        [
            pd.Series({"client_id": client_id, **unit_info})
            for client_id, unit_info in unit_vectors.items()
        ]
    ).set_index("client_id", drop=True)
    clustering = AgglomerativeClustering(n_clusters=n_clusters)

    scaler = StandardScaler()
    X_normalized = scaler.fit_transform(df.values)
    clusters = clustering.fit_predict(X_normalized)
    df["cluster"] = clusters

    for _cluster, cluster_group in df.groupby("cluster"):
        X_recovered = scaler.transform(cluster_group[cluster_group.columns[:-1]].values)
        centroid = X_recovered.mean(axis=0)
        centroid_distance = np.array(
            [np.linalg.norm(r - centroid, ord=2) for r in X_recovered]
        )
        cluster_group["center_dist"] = centroid_distance

        # find unit closest to center
        center_index = cluster_group["center_dist"].argmin()
        group = cluster_group.index
        centroid_unit = group[center_index]

        yield group.to_list(), centroid_unit
