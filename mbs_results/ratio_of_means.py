from typing import Dict

import pandas as pd

from src.apply_imputation_link import create_and_merge_imputation_values
from src.calculate_imputation_link import calculate_imputation_link
from src.construction_matches import flag_construction_matches
from src.cumulative_imputation_links import get_cumulative_links
from src.flag_and_count_matched_pairs import count_matches, flag_matched_pair
from src.imputation_flags import create_impute_flags, generate_imputation_marker
from src.predictive_variable import shift_by_strata_period


def wrap_flag_matched_pairs(
    df: pd.DataFrame, **default_columns: Dict[str, str]
) -> pd.DataFrame:
    """
    Wrapper function for flagging forward, backward and construction pair
    matches.

    Parameters
    ----------
    df : pd.DataFrame
        Original dataframe.
    **default_columns : Dict[str, str]
        The column names which were passed to ratio of means function.
    Returns
    -------
    df : pd.DataFrame
        Original dataframe with 4 bool columns, column names are
        forward_or_backward keyword and target column name to distinguish them
    """

    flag_arguments = [
        dict(**default_columns, **{"forward_or_backward": "f"}),
        dict(**default_columns, **{"forward_or_backward": "b"}),
    ]

    for args in flag_arguments:

        df = flag_matched_pair(df, **args)

    df = flag_construction_matches(df, **default_columns)

    return df


def wrap_count_matches(
    df: pd.DataFrame, **default_columns: Dict[str, str]
) -> pd.DataFrame:
    """Wrapper function to get counts of flagged matched pairs.

    Parameters
    ----------
    df : pd.DataFrame
        Original dataframe.
    **default_columns : Dict[str, str]
        The column names which were passed to ratio of means function.
    Returns
    -------
    df : pd.DataFrame
        Original dataframe with 3 new numeric columns.
    """

    count_arguments = (
        dict(**default_columns, **{"flag_column_name": "f_match"}),
        dict(**default_columns, **{"flag_column_name": "b_match"}),
        dict(**default_columns, **{"flag_column_name": "flag_construction_matches"}),
    )

    for args in count_arguments:
        df = count_matches(df, **args)

    return df


def wrap_shift_by_strata_period(
    df: pd.DataFrame, **default_columns: Dict[str, str]
) -> pd.DataFrame:
    """
    Wrapper function for shifting values.

    f_predictive_question: is used from calculate imputation link
    b_predictive_question: is used from calculate imputation link
    f_predictive_auxiliary: is used from create_impute_flags

    Parameters
    ----------
    df : pd.DataFrame
        Original dataframe.
    **default_columns : Dict[str, str]
        The column names kwargs which were passed to ratio of means function.

    Returns
    -------
    df : pd.DataFrame
        Original dataframe with 3 new numeric columns which contain the desired
        shifted values.
    """

    link_arguments = (
        dict(
            **default_columns,
            **{"time_difference": 1, "new_col": "f_predictive_question"}
        ),
        dict(
            **default_columns,
            **{"time_difference": -1, "new_col": "b_predictive_question"}
        ),
        # Needed for ccreate_impute_flags
        dict(
            **{**default_columns, "target": default_columns["auxiliary"]},
            **{"time_difference": 1, "new_col": "f_predictive_auxiliary"}
        ),
    )

    for args in link_arguments:
        df = shift_by_strata_period(df, **args)

    return df


def wrap_calculate_imputation_link(
    df: pd.DataFrame, **default_columns: Dict[str, str]
) -> pd.DataFrame:
    """Wrapper for calculate_imputation_link function.

    Parameters
    ----------
    df : pd.DataFrame
        Original dataframe.
    **default_columns : Dict[str, str]
        The column names which were passed to ratio of means function.

    Returns
    -------
    df : pd.DataFrame
        Original dataframe with 3 new numeric columns which contain the
        imputation links.
    """

    link_arguments = (
        dict(
            **default_columns,
            **{
                "match_col": "f_match",
                "predictive_variable": "f_predictive_question",
                "link_col_name": "f_link_question",
            }
        ),
        dict(
            **default_columns,
            **{
                "match_col": "b_match",
                "predictive_variable": "b_predictive_question",
                "link_col_name": "b_link_question",
            }
        ),
        dict(
            **default_columns,
            **{
                "match_col": "flag_construction_matches",
                "predictive_variable": "other",
                "link_col_name": "construction_link",
            }
        ),
    )

    for args in link_arguments:
        df = calculate_imputation_link(df, **args)

    return df


def wrap_get_cumulative_links(
    df: pd.DataFrame, **default_columns: Dict[str, str]
) -> pd.DataFrame:
    """Wrapper for calculate_imputation_link function.

    Parameters
    ----------
    df : pd.DataFrame
        Original dataframe.
    **default_columns : Dict[str, str]
        The column names kwargs which were passed to ratio of means function.

    Returns
    -------
    df : pd.DataFrame
        Original dataframe with 2 new numeric column, with the cummulative
        product of imputation links. These are needed when consecutive periods
        need imputing.
    """

    cum_links_arguments = (
        dict(
            **default_columns,
            **{"forward_or_backward": "f", "imputation_link": "f_link_question"}
        ),
        dict(
            **default_columns,
            **{"forward_or_backward": "b", "imputation_link": "b_link_question"}
        ),
    )

    for args in cum_links_arguments:

        df = get_cumulative_links(df, **args)

    return df


def ratio_of_means(
    df: pd.DataFrame,
    target: str,
    period: str,
    reference: str,
    strata: str,
    auxiliary: str,
) -> pd.DataFrame:
    """
    Imputes for each non-responding contributor a single numeric target
    variable within the dataset for multiple periods simultaneously. It uses
    the relationship between the target variable of interest and a predictive
    value and/or auxiliary variable to inform the imputed value. The method
    can apply forward, backward, construction or forward from construction
    imputation. The type of imputation used will vary for each non-respondent
    in each period depending on whether data is available in the predictive
    period

    Parameters
    ----------
    df : pd.DataFrame
         Original dataframe.
    target : str
        Column name of values to be imputed.
    period : str
        Column name containing datetime information.
    reference : str
        Column name of unique Identifier.
    strata : str
        Column name containing strata information (sic).
    auxiliary : str
        Column name containing auxiliary information (sic).

    Returns
    -------
    pd.DataFrame
        Original dataframe with imputed values in the target column, and with
        intermediate columns which were used for the imputation method.
    """

    # Saving args to dict, so we can pass same attributes to multiple functions
    # These arguments are used from the majority of functions
    # Removing though df since we are chaining function with pipe

    default_columns = locals()

    del default_columns["df"]

    # TODO: Is datetime needed? If so here is a good place to convert to datetime
    df["date"] = pd.to_datetime(df["date"], format="%Y%m")

    # TODO: Filter data out
    # TODO: Pre calculated links

    df = (
        df.pipe(wrap_flag_matched_pairs, **default_columns)
        # .pipe(wrap_count_matches, **default_columns) #needs to be seperated
        .pipe(wrap_shift_by_strata_period, **default_columns)
        .pipe(wrap_calculate_imputation_link, **default_columns)
        .pipe(
            create_impute_flags,
            **default_columns,
            predictive_auxiliary="f_predictive_auxiliary"
        )
        # TODO: How we gonna set defaults?
        .fillna(
            {"f_link_question": 1.0, "b_link_question": 1.0, "construction_link": 1.0}
        )
        .pipe(generate_imputation_marker)
        .pipe(wrap_get_cumulative_links, **default_columns)
        .pipe(
            create_and_merge_imputation_values,
            **default_columns,
            imputation_class="group",
            marker="imputation_marker",
            combined_imputation="imputed_value",
            cumulative_forward_link="cumulative_f_link_question",
            cumulative_backward_link="cumulative_b_link_question",
            construction_link="construction_link",
            imputation_types=("c", "fir", "bir", "fic")
        )
    )

    df = df.reset_index(drop=True)

    df["date"] = pd.to_numeric(df["date"].dt.strftime("%Y%m"), errors="coerce")

    df = df.drop(
        columns=[
            "f_match",
            "b_match",
            "flag_construction_matches",
            "r_flag",
            "fir_flag",
            "bir_flag",
            "c_flag",
            "fic_flag",
            "missing_value",
            "imputation_group",
            "cumulative_f_link_question",
            "cumulative_b_link_question",
            "f_predictive_question",
            "b_predictive_question",
            "f_predictive_question_roll",
            "b_predictive_question_roll",
        ]
    )

    # TODO: Missing extra columns, default values and if filter was applied, all bool

    return df
