import pandas as pd
import os
from data_ingestion_utils import check_schema_dataset, save_dataframe_as_csv, create_connection

def test_check_schema_dataset():
    # Updated schema according to the new structure
    schema = {
        "data":
        {
            "clinical":{
                "ID":["string"],	
                "WHO 2016":["category"],	
                "WHO 2016 label":["string"],	
                "WHO 2022":["category"],	
                "WHO 2022 label":["string"],	
                "ICC 2022":["category"],	
                "ICC 2022 label":["string"],	
                "Qualifier":["string"],	
                "ELN 2017":["string"],	
                "ELN 2022":["string"],	
                "AGE":["float"],	
                "Intensive chemotherapy induction":["int"],	
                "Allogeneic HSCT":["int"],	
                "Autologous HSCT":["int"],	
                "Overall survival":["int"],	
                "TIME TO CR":["float"],	
                "TIME TO HSCT":["float"],
                "TIME TO RELAPSE":["float"],	
                "STATUS AT HSCT":["string"],	
                "TIME FROM CR1 TO HSCT":["float"],	
                "FAMILY DONOR":["float"],	
                "RESPONSE TO INDUCTION":["string"],
                "STATUS_OS":["int"],	
                "STATUS_EFS":["int"],	
                "EFS EVENT":["string"],	
                "TIME TO EFS":["int"],	
                "RFS STATUS":["float"],	
                "TIME TO RFS":["float"],	
                "HB":["float"],	
                "PLT":["float"],	
                "WBC":["float"],	
                "LDH":["float"],	
                "SEX":["int"],	
                "BM BLASTS":["float"],	
                "ECOG":["float"],	
                "PB BLASTS":["float"],	
                "SPLENOMEGALY":["float"]
                },	
            "karyotype":{
                "KARYOTYPE": ["string"],
                "complex" : ["int"],	
                "inv3_t3_3": ["int"],	
                "t_9_22": ["int"],	
                "minus5_5q": ["int"],	
                "mono7": ["int"],	
                "del7q": ["int"],	
                "7other": ["int"],	
                "plus8_8q": ["int"],	
                "del9q": ["int"],	
                "mono12_12p_abn12p": ["int"],	
                "plus13": ["int"],	
                "mono17_17p_abn17p": ["int"],	
                "mono18_18q": ["int"],	
                "mono20_20q": ["int"],	
                "plus21": ["int"],	
                "plus22": ["int"],	
                "monoY": ["int"],	
                "t_15_17": ["int"],	
                "t_8_21": ["int"],	
                "inv16_t16_16": ["int"],	
                "t_6_9": ["int"],	
                "abn3q_other": ["int"],	
                "plus11_11q": ["int"],	
                "mono4_4q_abn(4q)": ["int"],	
                "var_recurr_balanced": ["int"],	
                "var_recurr_unbalanced": ["int"],	
                "MLL_REARRANGED": ["int"],	
                "anomaly chr 1": ["int"],	
                "anomaly chr 2": ["int"],
                "anomaly chr 3": ["int"],	
                "anomaly chr 4": ["int"],	
                "anomaly chr 5": ["int"],	
                "anomaly chr 6": ["int"],	
                "anomaly chr 7": ["int"],
                "anomaly chr 8": ["int"],	
                "anomaly chr 9": ["int"],	
                "anomaly chr 10": ["int"],	
                "anomaly chr 11": ["int"],	
                "anomaly chr 12": ["int"],	
                "anomaly chr 13": ["int"],	
                "anomaly chr 14": ["int"],	
                "anomaly chr 15": ["int"],	
                "anomaly chr 16": ["int"],	
                "anomaly chr 17": ["int"],	
                "anomaly chr 18": ["int"],	
                "anomaly chr 19": ["int"],	
                "anomaly chr 20": ["int"],	
                "anomaly chr 21": ["int"],	
                "anomaly chr 22": ["int"],	
                "anomaly chr x": ["int"],	
                "anomaly chr y": ["int"]
                },
            "mutations":{	
                "ASXL1": ["int"],	
                "ATRX": ["int"],	
                "BCOR": ["int"],	
                "BRAF": ["int"],	
                "CBL": ["int"],	
                "CBLB": ["int"],	
                "CDKN2A": ["int"],	
                "CEBPA_bi": ["int"],	
                "CREBBP": ["int"],	
                "CUX1": ["int"],	
                "DNMT3A": ["int"],	
                "EP300": ["int"],	
                "ETV6": ["int"],	
                "EZH2": ["int"],	
                "FBXW7": ["int"],	
                "FLT3_ITD": ["int"],	
                "FLT3_TKD": ["int"],	
                "GATA2": ["int"],	
                "GNAS": ["int"],	
                "IDH1": ["int"],	
                "IDH2": ["int"],	
                "IKZF1": ["int"],	
                "JAK2": ["int"],	
                "KDM5A": ["int"],	
                "KDM6A": ["int"],	
                "KIT": ["int"],	
                "KRAS": ["int"],	
                "MLL": ["int"],	
                "MLL2": ["int"],	
                "MLL3": ["int"],	
                "MLL5": ["int"],	
                "MPL": ["int"],	
                "MYC": ["int"],	
                "NF1": ["int"],	
                "NPM1": ["int"],	
                "NRAS": ["int"],	
                "PHF6": ["int"],	
                "PRPF40B": ["int"],	
                "PTEN": ["int"],	
                "PTPN11": ["int"],	
                "RAD21": ["int"],	
                "RB1": ["int"],	
                "RUNX1": ["int"],	
                "SF1": ["int"],	
                "SF3A1": ["int"],	
                "SF3B1": ["int"],	
                "SH2B3": ["int"],	
                "SRSF2": ["int"],	
                "STAG2": ["int"],	
                "TET2": ["int"],	
                "TP53": ["int"],	
                "U2AF1": ["int"],	
                "U2AF2": ["int"],	
                "WT1": ["int"],	
                "ZRSR2": ["int"]
                }
            }
        }

    # Sample data for testing
    data = {
        "ID": ["ID1", "ID2", "ID3"],
        "WHO 2016": [12, 12, 12],
        "WHO 2016 label": ["AML with myelodysplasia-related changes", "AML with myelodysplasia-related changes ", "AML with myelodysplasia-related changes"],
        "WHO 2022": [12, 12, 12],
        "WHO 2022 label": ["Acute myeloid leukaemia, myelodysplasia-related", "Acute myeloid leukaemia, myelodysplasia-related", "Acute myeloid leukaemia, myelodysplasia-related"],
        "ICC 2022": [14, 14, 14],
        "ICC 2022 label": ["AML with mutated TP53", "AML with mutated TP53", "AML with mutated TP53"],
        "Qualifier": ["adverse", "adverse", "adverse"],
        "KARYOTYPE": ["~44,XX,del(3)(q21),-4,add(5)(q13),add(7)(p22),-15,-17,add(19)(q13),+21", 
                      "~49,X,add(X)(q28),del(2)(p23),del(7)(q11),na,add(14)(p11),del(16)(p13),add(17)(p11),add(19)(p13),+4mar", 
                      "~59,X,-X,-X,-1,-3,-4,-5,-6,-7,-12,-14,-16,-17,2xadd(21)(p11),+2mar"],
        "complex": [1, 0.4, 1],
        "inv3_t3_3": [0, 1, 0],
        "ASXL1": [0, 1.9, 0],
        "ATRX": [1, 0, 1]
    }

    # Combining all data into a single DataFrame
    df_clinical = pd.DataFrame({
        "ID": data["ID"],
        "WHO 2016": data["WHO 2016"],
        "WHO 2016 label": data["WHO 2016 label"],
        "WHO 2022": data["WHO 2022"],
        "WHO 2022 label": data["WHO 2022 label"],
        "ICC 2022": data["ICC 2022"],
        "ICC 2022 label": data["ICC 2022 label"],
        "Qualifier": data["Qualifier"]
    })

    df_karyotype = pd.DataFrame({
        "KARYOTYPE": data["KARYOTYPE"],
        "complex": data["complex"],
        "inv3_t3_3": data["inv3_t3_3"]
    })

    df_mutations = pd.DataFrame({
        "ASXL1": data["ASXL1"],
        "ATRX": data["ATRX"]
    })

    # Assuming check_schema_dataset can handle different DataFrames for each schema section
    errors_clinical = list(check_schema_dataset(schema["data"]["clinical"], df_clinical))
    errors_karyotype = list(check_schema_dataset(schema["data"]["karyotype"], df_karyotype))
    errors_mutations = list(check_schema_dataset(schema["data"]["mutations"], df_mutations))

    assert len(errors_clinical) == 0
    assert len(errors_karyotype) == 0
    assert len(errors_mutations) == 0

def test_save_dataframe_as_csv(tmp_path):
    # Create sample data according to the updated schema
    data = {
        "ID": ["ID1", "ID2", "ID3"],
        "WHO 2016": [12, 12, 12],
        "WHO 2016 label": ["AML with myelodysplasia-related changes", "AML with myelodysplasia-related changes ", "AML with myelodysplasia-related changes"],
        "WHO 2022": [12, 12, 12],
        "WHO 2022 label": ["Acute myeloid leukaemia, myelodysplasia-related", "Acute myeloid leukaemia, myelodysplasia-related", "Acute myeloid leukaemia, myelodysplasia-related"],
        "ICC 2022": [14, 14, 14],
        "ICC 2022 label": ["AML with mutated TP53", "AML with mutated TP53", "AML with mutated TP53"],
        "Qualifier": ["adverse", "adverse", "adverse"],
        "KARYOTYPE": ["~44,XX,del(3)(q21),-4,add(5)(q13),add(7)(p22),-15,-17,add(19)(q13),+21", 
                      "~49,X,add(X)(q28),del(2)(p23),del(7)(q11),na,add(14)(p11),del(16)(p13),add(17)(p11),add(19)(p13),+4mar", 
                      "~59,X,-X,-X,-1,-3,-4,-5,-6,-7,-12,-14,-16,-17,2xadd(21)(p11),+2mar"],
        "complex": [1, 0.4, 1],
        "inv3_t3_3": [0, 1, 0],
        "ASXL1": [0, 1.9, 0],
        "ATRX": [1, 0, 1]
    }

    # Combine all data into a single DataFrame for saving
    df = pd.DataFrame(data)

    # Save the DataFrame as a CSV file
    filename = "test.csv"
    node = "node1"
    filepath = save_dataframe_as_csv(df, filename, node)

    # Assert that the file was created
    assert os.path.exists(filepath)

    # Optionally, read the file and check its content
    saved_df = pd.read_csv(filepath)
    pd.testing.assert_frame_equal(df, saved_df)

def test_create_connection():
    conn = create_connection()
    assert conn is not None
    conn.close()
