import json
import re
import unicodedata
from datetime import date, datetime
from zoneinfo import ZoneInfo

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


SPREADSHEET_ID = "12iZXbTp2duwhWSoi9grjL5FFRbOvLlU1u4IBZvKkHlw"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


# =========================================================
# NORMALIZAÇÃO
# =========================================================
def normalizar_coluna(valor):
    texto = str(valor or "").strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    ).encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)

    return texto.strip("_")


def normalizar_ra(valor):
    if valor is None:
        return ""

    texto = str(valor).strip()

    if texto.lower() in {
        "",
        "nan",
        "none",
        "null",
    }:
        return ""

    if re.fullmatch(r"\d+\.0+", texto):
        texto = texto.split(".")[0]

    return texto


def valor_vazio(valor):
    if valor is None:
        return True

    try:
        if pd.isna(valor):
            return True
    except Exception:
        pass

    return str(valor).strip().lower() in {
        "",
        "nan",
        "none",
        "null",
    }


def serializar_valor(valor):
    if valor is None:
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    if isinstance(valor, (date, datetime)):
        return valor.strftime("%Y-%m-%d")

    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass

    return str(valor).strip()


def encontrar_coluna(df, candidatos):
    if df is None or df.empty:
        return None

    mapa_colunas = {
        normalizar_coluna(coluna): coluna
        for coluna in df.columns
    }

    for candidato in candidatos:
        candidato_normalizado = normalizar_coluna(
            candidato
        )

        if candidato_normalizado in mapa_colunas:
            return mapa_colunas[candidato_normalizado]

    return None


def criar_headers_unicos(headers):
    headers_resultado = []
    contagem = {}

    for indice, header in enumerate(headers):
        nome = str(header).strip()

        if not nome:
            nome = f"coluna_{indice + 1}"

        if nome not in contagem:
            contagem[nome] = 1
            headers_resultado.append(nome)
            continue

        contagem[nome] += 1

        headers_resultado.append(
            f"{nome}_{contagem[nome]}"
        )

    return headers_resultado


# =========================================================
# AUTENTICAÇÃO
# =========================================================
@st.cache_resource(show_spinner=False)
def criar_cliente_google():
    if "google_credentials_json" not in st.secrets:
        raise KeyError(
            "A configuração 'google_credentials_json' "
            "não foi encontrada no secrets.toml."
        )

    credentials_info = json.loads(
        st.secrets["google_credentials_json"]
    )

    credentials = Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES,
    )

    return gspread.authorize(credentials)


@st.cache_resource(show_spinner=False)
def abrir_planilha():
    cliente = criar_cliente_google()

    return cliente.open_by_key(
        SPREADSHEET_ID
    )


# =========================================================
# LEITURA
# =========================================================
@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def listar_abas():
    planilha = abrir_planilha()

    return [
        worksheet.title
        for worksheet in planilha.worksheets()
    ]


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_aba(nome_aba):
    planilha = abrir_planilha()

    try:
        worksheet = planilha.worksheet(
            nome_aba
        )

    except gspread.WorksheetNotFound as error:
        raise KeyError(
            f"A aba '{nome_aba}' não foi encontrada."
        ) from error

    valores = worksheet.get_all_values()

    if not valores:
        return pd.DataFrame()

    total_colunas = max(
        len(linha)
        for linha in valores
    )

    header_original = valores[0] + (
        [""] * (
            total_colunas
            - len(valores[0])
        )
    )

    headers = criar_headers_unicos(
        header_original
    )

    linhas = []

    for linha in valores[1:]:
        linha_ajustada = linha + (
            [""] * (
                total_colunas
                - len(linha)
            )
        )

        linhas.append(linha_ajustada)

    return pd.DataFrame(
        linhas,
        columns=headers,
    )


# =========================================================
# BASES
# =========================================================
@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_base_alunos():
    return carregar_aba("BASE_ALUNOS")


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_base_alunos_ativos():
    df = carregar_base_alunos()

    if df.empty:
        return df.copy()

    coluna_status = encontrar_coluna(
        df,
        ["Status_PREP"],
    )

    if coluna_status is None:
        raise KeyError(
            "A coluna Status_PREP não foi encontrada "
            "na aba BASE_ALUNOS."
        )

    status_normalizado = (
        df[coluna_status]
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    df_ativos = df.loc[
        status_normalizado == "ativo"
    ].copy()

    coluna_ra = encontrar_coluna(
        df_ativos,
        ["RA"],
    )

    if coluna_ra is not None:
        df_ativos[coluna_ra] = (
            df_ativos[coluna_ra]
            .apply(normalizar_ra)
        )

    return df_ativos.reset_index(
        drop=True
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_application():
    df = carregar_aba("APPLICATION")

    coluna_ra = encontrar_coluna(
        df,
        ["RA"],
    )

    if coluna_ra is not None:
        df[coluna_ra] = (
            df[coluna_ra]
            .apply(normalizar_ra)
        )

    return df


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_pre_application():
    df = carregar_aba("PRE-APPLICATION")

    coluna_ra = encontrar_coluna(
        df,
        ["RA"],
    )

    if coluna_ra is not None:
        df[coluna_ra] = (
            df[coluna_ra]
            .apply(normalizar_ra)
        )

    return df


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_sats():
    df = carregar_aba("SATs")

    coluna_ra = encontrar_coluna(
        df,
        ["RA"],
    )

    if coluna_ra is not None:
        df[coluna_ra] = (
            df[coluna_ra]
            .apply(normalizar_ra)
        )

    return df


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_atendimentos():
    return carregar_aba("ATENDIMENTOS")


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_students_application():
    return carregar_aba(
        "Students_Application"
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def carregar_prep_students():
    df = carregar_aba(
        "Prep_Students"
    )

    coluna_ra = encontrar_coluna(
        df,
        ["RA"],
    )

    if coluna_ra is not None:
        df[coluna_ra] = (
            df[coluna_ra]
            .apply(normalizar_ra)
        )

    return df


# =========================================================
# GRAVAÇÃO DE ATENDIMENTOS
# =========================================================
def garantir_colunas_atendimentos(
    worksheet,
):
    colunas_necessarias = [
        "Nome | RA",
        "RA",
        "Responsável pelo atendimento",
        "Tipo de Atendimento",
        "Registro do atendimento",
        "Data do atendimento",
        "Data do registro",
    ]

    headers = [
        str(header).strip()
        for header in worksheet.row_values(1)
    ]

    if not any(headers):
        worksheet.append_row(
            colunas_necessarias,
            value_input_option="USER_ENTERED",
        )

        return colunas_necessarias

    headers_normalizados = {
        normalizar_coluna(header): header
        for header in headers
        if header
    }

    for coluna in colunas_necessarias:
        coluna_normalizada = normalizar_coluna(
            coluna
        )

        if coluna_normalizada not in headers_normalizados:
            headers.append(coluna)

            worksheet.update_cell(
                1,
                len(headers),
                coluna,
            )

            headers_normalizados[
                coluna_normalizada
            ] = coluna

    return headers


def registrar_atendimento(
    nome_ra,
    responsavel_atendimento,
    tipo_atendimento,
    registro_atendimento,
    data_atendimento,
):
    planilha = abrir_planilha()

    try:
        worksheet = planilha.worksheet(
            "ATENDIMENTOS"
        )

    except gspread.WorksheetNotFound as error:
        raise KeyError(
            "A aba ATENDIMENTOS não foi encontrada."
        ) from error

    headers = garantir_colunas_atendimentos(
        worksheet
    )

    partes_nome_ra = [
        parte.strip()
        for parte in str(nome_ra).split("|")
    ]

    ra = (
        normalizar_ra(partes_nome_ra[-1])
        if len(partes_nome_ra) >= 2
        else ""
    )

    nome = (
        " | ".join(partes_nome_ra[:-1]).strip()
        if len(partes_nome_ra) >= 2
        else str(nome_ra).strip()
    )

    data_registro = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    valores = {
        "nome_ra": str(nome_ra).strip(),
        "nome": nome,
        "ra": ra,
        "responsavel_pelo_atendimento": (
            str(responsavel_atendimento).strip()
        ),
        "tipo_de_atendimento": (
            str(tipo_atendimento).strip()
        ),
        "registro_do_atendimento": (
            str(registro_atendimento).strip()
        ),
        "data_do_atendimento": (
            serializar_valor(data_atendimento)
        ),
        "data_do_registro": data_registro,
    }

    linha = []

    for header in headers:
        header_normalizado = normalizar_coluna(
            header
        )

        linha.append(
            valores.get(
                header_normalizado,
                "",
            )
        )

    worksheet.append_row(
        linha,
        value_input_option="USER_ENTERED",
    )

    carregar_aba.clear()
    carregar_atendimentos.clear()