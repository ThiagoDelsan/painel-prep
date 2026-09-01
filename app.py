from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from src.data import (
    carregar_application,
    carregar_atendimentos,
    carregar_base_alunos_ativos,
    carregar_pre_application,
    carregar_prep_students,
    carregar_sats,
    encontrar_coluna,
    normalizar_coluna,
    normalizar_ra,
    registrar_atendimento,
    valor_vazio,
)


# =========================================================
# CONFIGURAÇÃO
# =========================================================
st.set_page_config(
    page_title="Painel PREP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


PAGINAS = [
    "Indicadores Application",
    "Status Application",
    "Indicadores Pre-Application",
    "Dash Micro",
    "Registro de Atendimento",
    "Administrativo",
]


ICONES_PAGINAS = {
    "Indicadores Application": "📊",
    "Status Application": "📋",
    "Indicadores Pre-Application": "📊",
    "Dash Micro": "👥",
    "Registro de Atendimento": "📝",
    "Administrativo": "⚙️",
}


COLUNAS_FILTROS = [
    "Colégio",
    "Turma",
    "Ano",
    "Gênero",
    "Praça",
    "Cor/Raça",
]


CAMPOS_PREP = [
    "Education Status",
    "Family Income Range (per capita/month)",
    "GPA",
    "Intended Major 1",
    "Intended Major 2",
    "Intended Major 3",
]


INDICADORES_PRE_APPLICATION = [
    "9º",
    "Mock AC1",
    "DET Mock",
]


INDICADORES_APPLICATION = [
    "Math Max",
    "English Max",
    "Superscore",
    "Global",
    "DET",
]


MAPEAMENTO_STATUS_APPLICATION = {
    "Aluno": [
        "Aluno",
        "Nome",
        "Full Name",
    ],
    "Expectativa": [
        "Classificação Prep",
        "Expectativa",
    ],
    "Apoio Externo": [
        "Apoio Externo",
    ],
    "NOTAS": [
        "Global",
    ],
    "SAT": [
        "Superscore",
    ],
    "DET": [
        "DET",
    ],
    "Atividades": [
        "Atividades",
    ],
    "Engaj.": [
        "Engaj.",
        "Engajamento",
    ],
    "Obs.": [
        "Obs.",
        "Observação",
        "Observações",
    ],
}


CORES_EVENTOS = {
    "Atendimento": "#64748B",
    "SAT": "#2563EB",
}


# =========================================================
# ESTILOS
# =========================================================
def aplicar_estilos():
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            section[data-testid="stSidebar"] {
                background-color: #F6F8FB;
                border-right: 1px solid #E2E6EC;
            }

            section[data-testid="stSidebar"]
            div[class*="st-key-nav_main_"] {
                width: 100% !important;
                margin-top: -0.40rem !important;
                margin-bottom: -0.40rem !important;
                padding: 0 !important;
            }

            section[data-testid="stSidebar"]
            div[class*="st-key-nav_main_"] button {
                width: 100% !important;
                min-height: 1.75rem !important;
                display: flex !important;
                justify-content: flex-start !important;
                align-items: center !important;
                padding: 0.18rem 0.55rem !important;
                background: transparent !important;
                border: 0 !important;
                border-radius: 5px !important;
                box-shadow: none !important;
                color: #343946 !important;
                font-size: 0.77rem !important;
                text-align: left !important;
            }

            section[data-testid="stSidebar"]
            div[class*="st-key-nav_main_"] button > div,
            section[data-testid="stSidebar"]
            div[class*="st-key-nav_main_"]
            button [data-testid="stMarkdownContainer"] {
                width: 100% !important;
                display: flex !important;
                justify-content: flex-start !important;
                text-align: left !important;
            }

            section[data-testid="stSidebar"]
            div[class*="st-key-nav_main_"] button p,
            section[data-testid="stSidebar"]
            div[class*="st-key-nav_main_"] button span {
                width: 100% !important;
                margin: 0 !important;
                color: inherit !important;
                text-align: left !important;
            }

            section[data-testid="stSidebar"]
            div[class*="st-key-nav_main_"]
            button[kind="primary"] {
                background: #DCE1EA !important;
                color: #24364B !important;
            }

            section[data-testid="stSidebar"]
            div[class*="st-key-atualizar_dados"] button,
            section[data-testid="stSidebar"]
            div[class*="st-key-limpar_filtros"] button {
                width: 100% !important;
                min-height: 2.05rem !important;
                background: #FFFFFF !important;
                border: 1px solid #D7DBE3 !important;
                border-radius: 6px !important;
                color: #4B5160 !important;
                font-size: 0.75rem !important;
                font-weight: 600 !important;
            }

            div[data-testid="stTabs"]
            button[aria-selected="true"] {
                color: #60A5FA !important;
                font-weight: 700 !important;
            }

            div[data-testid="stMetric"] {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 0.75rem 1rem;
            }

            .timeline-marker {
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 72px;
                padding-top: 0.55rem;
            }

            .timeline-circle {
                width: 13px;
                height: 13px;
                border-radius: 50%;
            }

            .timeline-line {
                width: 2px;
                min-height: 55px;
                margin-top: 4px;
                background: #CBD5E1;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# FUNÇÕES GERAIS
# =========================================================
def formatar_inteiro(valor):
    return f"{int(valor):,}".replace(",", ".")


def formatar_resultado(valor):
    if valor_vazio(valor):
        return "—"

    texto = str(valor).strip()

    try:
        numero = float(
            texto.replace(",", ".")
        )

        if numero.is_integer():
            return str(int(numero))

        return f"{numero:.2f}".replace(".", ",")

    except ValueError:
        return texto


def converter_serie_numerica(serie):
    texto = (
        serie
        .astype(str)
        .str.strip()
        .str.replace(",", ".", regex=False)
    )

    texto = texto.replace(
        {
            "": pd.NA,
            "-": pd.NA,
            "–": pd.NA,
            "—": pd.NA,
            "nan": pd.NA,
            "None": pd.NA,
        }
    )

    return pd.to_numeric(
        texto,
        errors="coerce",
    )


def converter_data(valor):
    if valor_vazio(valor):
        return pd.NaT

    return pd.to_datetime(
        str(valor).strip(),
        errors="coerce",
        dayfirst=True,
    )


def formatar_data(
    valor_original,
    valor_convertido,
):
    if pd.notna(valor_convertido):
        return valor_convertido.strftime(
            "%d/%m/%Y"
        )

    if not valor_vazio(valor_original):
        return str(valor_original).strip()

    return "Sem data"


def sat_foi_realizado(valor):
    if valor_vazio(valor):
        return False

    texto = str(valor).strip()

    if texto in {
        "-",
        "–",
        "—",
    }:
        return False

    try:
        if float(
            texto.replace(",", ".")
        ) == 0:
            return False
    except ValueError:
        pass

    return True


def selecionar_pagina(pagina):
    st.session_state["pagina_atual"] = pagina


def inicializar_navegacao():
    if st.session_state.get(
        "pagina_atual"
    ) not in PAGINAS:
        st.session_state["pagina_atual"] = (
            PAGINAS[0]
        )


def limpar_cache():
    st.cache_data.clear()


# =========================================================
# FILTROS
# =========================================================
def obter_opcoes_filtro(df, coluna):
    if coluna not in df.columns:
        return []

    valores = (
        df[coluna]
        .astype(str)
        .str.strip()
    )

    valores = valores.loc[
        ~valores.str.casefold().isin(
            {
                "",
                "nan",
                "none",
                "null",
            }
        )
    ]

    return sorted(
        valores.unique().tolist(),
        key=lambda valor: valor.casefold(),
    )


def limpar_filtros():
    for indice in range(
        len(COLUNAS_FILTROS)
    ):
        st.session_state[
            f"filtro_{indice}"
        ] = []


def aplicar_filtros(df, filtros):
    resultado = df.copy()

    for coluna, selecionados in filtros.items():
        if (
            coluna not in resultado.columns
            or not selecionados
        ):
            continue

        valores = (
            resultado[coluna]
            .astype(str)
            .str.strip()
        )

        resultado = resultado.loc[
            valores.isin(selecionados)
        ].copy()

    return resultado.reset_index(
        drop=True
    )


def renderizar_sidebar(
    base_alunos_ativos,
):
    st.sidebar.markdown("## Painel PREP")

    st.sidebar.caption(
        f"{formatar_inteiro(len(base_alunos_ativos))} "
        "alunos ativos"
    )

    st.sidebar.markdown("---")

    pagina_atual = st.session_state[
        "pagina_atual"
    ]

    for indice, pagina in enumerate(
        PAGINAS
    ):
        st.sidebar.button(
            (
                f"{ICONES_PAGINAS[pagina]}  "
                f"{pagina}"
            ),
            key=f"nav_main_{indice}",
            use_container_width=True,
            type=(
                "primary"
                if pagina == pagina_atual
                else "secondary"
            ),
            on_click=selecionar_pagina,
            args=(pagina,),
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filtros")

    filtros = {}

    for indice, coluna in enumerate(
        COLUNAS_FILTROS
    ):
        if coluna not in base_alunos_ativos.columns:
            filtros[coluna] = []
            continue

        filtros[coluna] = st.sidebar.multiselect(
            coluna,
            options=obter_opcoes_filtro(
                base_alunos_ativos,
                coluna,
            ),
            key=f"filtro_{indice}",
            placeholder="Todos",
        )

    base_filtrada = aplicar_filtros(
        base_alunos_ativos,
        filtros,
    )

    st.sidebar.caption(
        f"{formatar_inteiro(len(base_filtrada))} "
        "alunos selecionados"
    )

    st.sidebar.button(
        "Limpar filtros",
        key="limpar_filtros",
        use_container_width=True,
        on_click=limpar_filtros,
    )

    st.sidebar.markdown("---")

    st.sidebar.button(
        "🔄 Atualizar dados",
        key="atualizar_dados",
        use_container_width=True,
        on_click=limpar_cache,
    )

    return base_filtrada


# =========================================================
# BASES POR ETAPA
# =========================================================
def filtrar_etapa_prep(
    base_alunos,
    etapa,
):
    coluna_turma_prep = encontrar_coluna(
        base_alunos,
        ["Turma_PREP"],
    )

    if coluna_turma_prep is None:
        return pd.DataFrame()

    valores_normalizados = (
        base_alunos[coluna_turma_prep]
        .astype(str)
        .apply(normalizar_coluna)
    )

    return base_alunos.loc[
        valores_normalizados
        == normalizar_coluna(etapa)
    ].copy()


def filtrar_resultados_por_alunos(
    resultados,
    base_alunos,
):
    if resultados.empty or base_alunos.empty:
        return pd.DataFrame()

    coluna_ra_resultados = encontrar_coluna(
        resultados,
        ["RA"],
    )

    coluna_ra_alunos = encontrar_coluna(
        base_alunos,
        ["RA"],
    )

    if (
        coluna_ra_resultados is None
        or coluna_ra_alunos is None
    ):
        return pd.DataFrame()

    ras_validos = set(
        base_alunos[coluna_ra_alunos]
        .apply(normalizar_ra)
        .loc[lambda serie: serie != ""]
    )

    mascara = (
        resultados[coluna_ra_resultados]
        .apply(normalizar_ra)
        .isin(ras_validos)
    )

    return resultados.loc[
        mascara
    ].copy()


# =========================================================
# DISTRIBUIÇÕES
# =========================================================
def construir_contagem(df, coluna):
    if coluna not in df.columns:
        return pd.DataFrame()

    categorias = (
        df[coluna]
        .astype(str)
        .str.strip()
        .replace(
            {
                "": "Não informado",
                "nan": "Não informado",
                "None": "Não informado",
            }
        )
    )

    return (
        categorias
        .value_counts(dropna=False)
        .rename_axis("Categoria")
        .reset_index(name="Quantidade")
        .sort_values(
            "Quantidade",
            ascending=False,
        )
    )


def grafico_contagem(df, coluna):
    contagem = construir_contagem(
        df,
        coluna,
    )

    if contagem.empty:
        st.info(
            f"Não há dados para {coluna}."
        )
        return

    altura = max(
        220,
        36 * len(contagem),
    )

    barras = (
        alt.Chart(contagem)
        .mark_bar(
            color="#4D8FCB",
            cornerRadiusEnd=3,
        )
        .encode(
            x=alt.X(
                "Quantidade:Q",
                axis=None,
                title=None,
            ),
            y=alt.Y(
                "Categoria:N",
                title=None,
                sort="-x",
            ),
            tooltip=[
                "Categoria:N",
                "Quantidade:Q",
            ],
        )
    )

    rotulos = (
        alt.Chart(contagem)
        .mark_text(
            align="left",
            dx=5,
            color="#334155",
        )
        .encode(
            x="Quantidade:Q",
            y=alt.Y(
                "Categoria:N",
                sort="-x",
            ),
            text="Quantidade:Q",
        )
    )

    st.altair_chart(
        (
            barras + rotulos
        ).properties(
            height=altura,
        ),
        use_container_width=True,
    )


def renderizar_distribuicoes(
    base_etapa,
):
    if base_etapa.empty:
        st.info(
            "Nenhum aluno encontrado."
        )
        return

    st.caption(
        f"{formatar_inteiro(len(base_etapa))} "
        "alunos considerados"
    )

    for inicio in range(
        0,
        len(COLUNAS_FILTROS),
        2,
    ):
        colunas = st.columns(2)

        for deslocamento in range(2):
            indice = inicio + deslocamento

            if indice >= len(
                COLUNAS_FILTROS
            ):
                continue

            variavel = COLUNAS_FILTROS[
                indice
            ]

            with colunas[deslocamento]:
                st.markdown(
                    f"#### {variavel}"
                )

                grafico_contagem(
                    base_etapa,
                    variavel,
                )


# =========================================================
# BOXPLOTS
# =========================================================
def renderizar_boxplot(
    df,
    indicador,
):
    coluna = encontrar_coluna(
        df,
        [indicador],
    )

    if coluna is None:
        st.warning(
            f"A coluna {indicador} não foi encontrada."
        )
        return

    valores = converter_serie_numerica(
        df[coluna]
    ).dropna()

    if valores.empty:
        st.info(
            f"Não há resultados para {indicador}."
        )
        return

    media = valores.mean()

    dados_grafico = pd.DataFrame(
        {
            "Indicador": indicador,
            "Resultado": valores,
        }
    )

    dados_media = pd.DataFrame(
        {
            "Indicador": [indicador],
            "Média": [media],
            "Rótulo": [
                (
                    f"Média: {media:.2f}"
                    .replace(".", ",")
                )
            ],
        }
    )

    boxplot = (
        alt.Chart(dados_grafico)
        .mark_boxplot(
            extent="min-max",
            size=65,
            color="#4D8FCB",
        )
        .encode(
            x=alt.X(
                "Indicador:N",
                axis=None,
                title=None,
            ),
            y=alt.Y(
                "Resultado:Q",
                title=None,
                scale=alt.Scale(
                    zero=False,
                ),
            ),
        )
    )

    ponto_media = (
        alt.Chart(dados_media)
        .mark_point(
            shape="diamond",
            size=130,
            filled=True,
            color="#DC2626",
        )
        .encode(
            x=alt.X(
                "Indicador:N",
                axis=None,
            ),
            y=alt.Y(
                "Média:Q",
            ),
            tooltip=[
                alt.Tooltip(
                    "Média:Q",
                    title="Média",
                    format=".2f",
                ),
            ],
        )
    )

    rotulo_media = (
        alt.Chart(dados_media)
        .mark_text(
            dy=-16,
            color="#DC2626",
            fontSize=12,
            fontWeight="bold",
        )
        .encode(
            x="Indicador:N",
            y="Média:Q",
            text="Rótulo:N",
        )
    )

    grafico = (
        boxplot
        + ponto_media
        + rotulo_media
    ).properties(
        height=300,
    )

    st.altair_chart(
        grafico,
        use_container_width=True,
    )

    st.caption(
        f"N = {formatar_inteiro(len(valores))}"
    )


def renderizar_boxplots(
    df,
    indicadores,
):
    if df.empty:
        st.info(
            "Não há resultados disponíveis "
            "para os alunos selecionados."
        )
        return

    for inicio in range(
        0,
        len(indicadores),
        3,
    ):
        colunas = st.columns(3)

        grupo = indicadores[
            inicio:inicio + 3
        ]

        for coluna_layout, indicador in zip(
            colunas,
            grupo,
        ):
            with coluna_layout:
                st.markdown(
                    f"#### {indicador}"
                )

                renderizar_boxplot(
                    df,
                    indicador,
                )


def renderizar_resultados_etapa(
    base_etapa,
    etapa,
):
    try:
        if etapa == "Application":
            resultados = carregar_application()
            indicadores = INDICADORES_APPLICATION

        else:
            resultados = carregar_pre_application()
            indicadores = INDICADORES_PRE_APPLICATION

        resultados_filtrados = (
            filtrar_resultados_por_alunos(
                resultados,
                base_etapa,
            )
        )

        renderizar_boxplots(
            resultados_filtrados,
            indicadores,
        )

        st.info(
            "Posteriormente, serão incluídos "
            "boxplots comparativos com os anos "
            "anteriores. Esses dados ainda não "
            "estão disponíveis."
        )

    except Exception as error:
        st.error(
            "Não foi possível carregar os resultados."
        )

        st.error(
            f"{type(error).__name__}: {error}"
        )


def renderizar_pagina_indicadores(
    base_alunos_filtrada,
    etapa,
):
    st.title(
        f"Indicadores {etapa}"
    )

    base_etapa = filtrar_etapa_prep(
        base_alunos_filtrada,
        etapa,
    )

    tab_distribuicao, tab_resultados = (
        st.tabs(
            [
                "Distribuição",
                "Resultados",
            ]
        )
    )

    with tab_distribuicao:
        renderizar_distribuicoes(
            base_etapa
        )

    with tab_resultados:
        renderizar_resultados_etapa(
            base_etapa,
            etapa,
        )


# =========================================================
# STATUS APPLICATION
# =========================================================
def obter_valor_linha(
    linha,
    candidatos,
):
    if linha is None:
        return ""

    mapa = {
        normalizar_coluna(coluna): coluna
        for coluna in linha.index
    }

    for candidato in candidatos:
        chave = normalizar_coluna(
            candidato
        )

        if chave in mapa:
            return linha.get(
                mapa[chave],
                "",
            )

    return ""


def construir_tabela_status_application(
    base_application,
    application,
):
    if base_application.empty:
        return pd.DataFrame(
            columns=list(
                MAPEAMENTO_STATUS_APPLICATION.keys()
            )
        )

    coluna_ra_base = encontrar_coluna(
        base_application,
        ["RA"],
    )

    coluna_nome_base = encontrar_coluna(
        base_application,
        ["Nome", "Aluno"],
    )

    coluna_ra_application = encontrar_coluna(
        application,
        ["RA"],
    )

    application_por_ra = {}

    if coluna_ra_application is not None:
        for _, registro in application.iterrows():
            ra = normalizar_ra(
                registro.get(
                    coluna_ra_application,
                    "",
                )
            )

            if ra and ra not in application_por_ra:
                application_por_ra[ra] = registro

    linhas = []

    for _, aluno_base in base_application.iterrows():
        ra = (
            normalizar_ra(
                aluno_base.get(
                    coluna_ra_base,
                    "",
                )
            )
            if coluna_ra_base is not None
            else ""
        )

        registro_application = (
            application_por_ra.get(ra)
        )

        linha_saida = {}

        for nome_saida, candidatos in (
            MAPEAMENTO_STATUS_APPLICATION.items()
        ):
            valor = obter_valor_linha(
                registro_application,
                candidatos,
            )

            if (
                nome_saida == "Aluno"
                and valor_vazio(valor)
                and coluna_nome_base is not None
            ):
                valor = aluno_base.get(
                    coluna_nome_base,
                    "",
                )

            linha_saida[nome_saida] = (
                ""
                if valor_vazio(valor)
                else str(valor).strip()
            )

        linhas.append(linha_saida)

    tabela = pd.DataFrame(
        linhas,
        columns=list(
            MAPEAMENTO_STATUS_APPLICATION.keys()
        ),
    )

    return tabela.sort_values(
        "Aluno",
        key=lambda serie: (
            serie.astype(str).str.casefold()
        ),
    ).reset_index(drop=True)


def renderizar_status_application(
    base_alunos_filtrada,
):
    st.title("Status Application")

    base_application = filtrar_etapa_prep(
        base_alunos_filtrada,
        "Application",
    )

    try:
        application = carregar_application()

    except Exception as error:
        st.error(
            "Não foi possível carregar a aba APPLICATION."
        )

        st.error(
            f"{type(error).__name__}: {error}"
        )
        return

    tabela = construir_tabela_status_application(
        base_application,
        application,
    )

    if tabela.empty:
        st.info(
            "Nenhum aluno de Application foi "
            "encontrado para os filtros selecionados."
        )
        return

    st.caption(
        f"{formatar_inteiro(len(tabela))} alunos"
    )

    tabela_estilizada = (
        tabela.style
        .set_properties(
            **{
                "text-align": "center",
                "font-size": "12px",
            }
        )
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        (
                            "text-align",
                            "center",
                        ),
                    ],
                },
            ]
        )
    )

    st.dataframe(
        tabela_estilizada,
        use_container_width=True,
        hide_index=True,
        height=min(
            700,
            38 + 35 * len(tabela),
        ),
        column_config={
            "Aluno": st.column_config.TextColumn(
                "Aluno",
                width="large",
            ),
            "Expectativa": st.column_config.TextColumn(
                "Expectativa",
                width="medium",
            ),
            "Apoio Externo": st.column_config.TextColumn(
                "Apoio Externo",
                width="medium",
            ),
            "NOTAS": st.column_config.TextColumn(
                "NOTAS",
                width="small",
            ),
            "SAT": st.column_config.TextColumn(
                "SAT",
                width="small",
            ),
            "DET": st.column_config.TextColumn(
                "DET",
                width="small",
            ),
            "Atividades": st.column_config.TextColumn(
                "Atividades",
                width="medium",
            ),
            "Engaj.": st.column_config.TextColumn(
                "Engaj.",
                width="small",
            ),
            "Obs.": st.column_config.TextColumn(
                "Obs.",
                width="large",
            ),
        },
    )


# =========================================================
# SELEÇÃO DE ALUNOS
# =========================================================
def construir_opcoes_alunos(
    base_alunos,
):
    coluna_ra = encontrar_coluna(
        base_alunos,
        ["RA"],
    )

    coluna_nome = encontrar_coluna(
        base_alunos,
        ["Nome", "Aluno"],
    )

    coluna_nome_ra = encontrar_coluna(
        base_alunos,
        ["Nome_RA", "Nome | RA"],
    )

    opcoes = []
    mapa = {}

    for _, aluno in base_alunos.iterrows():
        ra = normalizar_ra(
            aluno.get(
                coluna_ra,
                "",
            )
        )

        nome = str(
            aluno.get(
                coluna_nome,
                "",
            )
        ).strip()

        nome_ra = str(
            aluno.get(
                coluna_nome_ra,
                "",
            )
        ).strip()

        rotulo = (
            nome_ra
            or (
                f"{nome} | {ra}"
                if nome and ra
                else nome or ra
            )
        )

        if not rotulo:
            continue

        opcoes.append(rotulo)

        mapa[rotulo] = {
            "nome": nome,
            "ra": ra,
            "rotulo": rotulo,
        }

    return (
        sorted(
            set(opcoes),
            key=str.casefold,
        ),
        mapa,
    )


def selecionar_aluno(
    base_alunos,
    key,
):
    opcoes, mapa = construir_opcoes_alunos(
        base_alunos
    )

    if not opcoes:
        st.warning(
            "Nenhum aluno disponível."
        )
        return None

    placeholder = "Selecione um aluno"

    opcoes_widget = [
        placeholder,
        *opcoes,
    ]

    if st.session_state.get(
        key
    ) not in opcoes_widget:
        st.session_state.pop(
            key,
            None,
        )

    selecionado = st.selectbox(
        "Aluno",
        opcoes_widget,
        key=key,
    )

    if selecionado == placeholder:
        return None

    return mapa[selecionado]


# =========================================================
# REGISTRO DE ATENDIMENTO
# =========================================================
def renderizar_registro_atendimento(
    base_alunos,
):
    st.title(
        "Registro de Atendimento"
    )

    opcoes, _ = construir_opcoes_alunos(
        base_alunos
    )

    if not opcoes:
        st.warning(
            "Nenhum aluno disponível."
        )
        return

    with st.form(
        "form_registro_atendimento",
        clear_on_submit=True,
    ):
        aluno = st.selectbox(
            "Nome | RA",
            [
                "Selecione um aluno",
                *opcoes,
            ],
        )

        responsavel = st.text_input(
            "Responsável pelo atendimento"
        )

        tipo = st.text_input(
            "Tipo de Atendimento"
        )

        registro = st.text_area(
            "Registro do Atendimento",
            height=180,
        )

        data_atendimento = st.date_input(
            "Data do atendimento",
            value=date.today(),
            format="DD/MM/YYYY",
        )

        enviar = st.form_submit_button(
            "Registrar atendimento",
            use_container_width=True,
        )

    if not enviar:
        return

    if (
        aluno == "Selecione um aluno"
        or not responsavel.strip()
        or not tipo.strip()
        or not registro.strip()
    ):
        st.error(
            "Preencha todos os campos obrigatórios."
        )
        return

    try:
        registrar_atendimento(
            nome_ra=aluno,
            responsavel_atendimento=responsavel,
            tipo_atendimento=tipo,
            registro_atendimento=registro,
            data_atendimento=data_atendimento,
        )

        st.cache_data.clear()

        st.success(
            "Atendimento registrado com sucesso!"
        )

    except Exception as error:
        st.error(
            f"Não foi possível registrar: {error}"
        )


# =========================================================
# CONSULTAS INDIVIDUAIS
# =========================================================
def obter_linha_por_ra(df, ra):
    if df.empty:
        return None

    coluna_ra = encontrar_coluna(
        df,
        ["RA"],
    )

    if coluna_ra is None:
        return None

    registros = df.loc[
        df[coluna_ra].apply(normalizar_ra)
        == normalizar_ra(ra)
    ]

    if registros.empty:
        return None

    return registros.iloc[0]


# =========================================================
# EVENTOS
# =========================================================
def construir_eventos_sat(linha_sat):
    if linha_sat is None:
        return []

    eventos = []

    for tentativa in range(1, 9):
        data_sat = obter_valor_linha(
            linha_sat,
            [
                f"SAT {tentativa}",
                f"SAT_{tentativa}",
            ],
        )

        if not sat_foi_realizado(
            data_sat
        ):
            continue

        eventos.append(
            {
                "tipo": "SAT",
                "titulo": f"SAT_{tentativa}",
                "data_original": data_sat,
                "data": converter_data(data_sat),
                "math": obter_valor_linha(
                    linha_sat,
                    [f"Math_{tentativa}"],
                ),
                "english": obter_valor_linha(
                    linha_sat,
                    [f"English_{tentativa}"],
                ),
            }
        )

    return eventos


def extrair_ra_nome_ra(valor):
    texto = str(valor).strip()

    if "|" not in texto:
        return ""

    return normalizar_ra(
        texto.split("|")[-1]
    )


def construir_eventos_atendimentos(
    atendimentos,
    ra,
):
    if atendimentos.empty:
        return []

    coluna_ra = encontrar_coluna(
        atendimentos,
        ["RA"],
    )

    coluna_nome_ra = encontrar_coluna(
        atendimentos,
        ["Nome | RA"],
    )

    if coluna_ra is not None:
        mascara = (
            atendimentos[coluna_ra]
            .apply(normalizar_ra)
            == normalizar_ra(ra)
        )

    elif coluna_nome_ra is not None:
        mascara = (
            atendimentos[coluna_nome_ra]
            .apply(extrair_ra_nome_ra)
            == normalizar_ra(ra)
        )

    else:
        return []

    registros = atendimentos.loc[
        mascara
    ]

    coluna_data = encontrar_coluna(
        atendimentos,
        ["Data do atendimento"],
    )

    coluna_responsavel = encontrar_coluna(
        atendimentos,
        ["Responsável pelo atendimento"],
    )

    coluna_tipo = encontrar_coluna(
        atendimentos,
        ["Tipo de Atendimento"],
    )

    coluna_registro = encontrar_coluna(
        atendimentos,
        ["Registro do atendimento"],
    )

    eventos = []

    for _, registro in registros.iterrows():
        data_original = (
            registro.get(
                coluna_data,
                "",
            )
            if coluna_data is not None
            else ""
        )

        eventos.append(
            {
                "tipo": "Atendimento",
                "titulo": "Atendimento",
                "data_original": data_original,
                "data": converter_data(
                    data_original
                ),
                "responsavel": (
                    registro.get(
                        coluna_responsavel,
                        "",
                    )
                    if coluna_responsavel is not None
                    else ""
                ),
                "tipo_atendimento": (
                    registro.get(
                        coluna_tipo,
                        "",
                    )
                    if coluna_tipo is not None
                    else ""
                ),
                "registro": (
                    registro.get(
                        coluna_registro,
                        "",
                    )
                    if coluna_registro is not None
                    else ""
                ),
            }
        )

    return eventos


# =========================================================
# DASH MICRO
# =========================================================
def renderizar_informacoes_prep(
    linha_prep,
):
    st.markdown(
        "### Informações do PREP"
    )

    valores = [
        (
            campo,
            formatar_resultado(
                obter_valor_linha(
                    linha_prep,
                    [campo],
                )
            ),
        )
        for campo in CAMPOS_PREP
    ]

    for inicio in range(
        0,
        len(valores),
        3,
    ):
        colunas = st.columns(3)

        for coluna, (
            campo,
            valor,
        ) in zip(
            colunas,
            valores[inicio:inicio + 3],
        ):
            with coluna:
                with st.container(
                    border=True
                ):
                    st.caption(campo)
                    st.markdown(
                        f"**{valor}**"
                    )


def renderizar_timeline(eventos):
    st.markdown("### Linha do tempo")

    if not eventos:
        st.info(
            "Não há eventos registrados."
        )
        return

    eventos = sorted(
        eventos,
        key=lambda evento: (
            evento["data"]
            if pd.notna(evento["data"])
            else pd.Timestamp("1900-01-01")
        ),
        reverse=True,
    )

    for indice, evento in enumerate(eventos):
        data_label = formatar_data(
            evento["data_original"],
            evento["data"],
        )

        coluna_eixo, coluna_conteudo = (
            st.columns(
                [0.045, 0.955],
                gap="small",
            )
        )

        with coluna_eixo:
            linha = (
                '<div class="timeline-line"></div>'
                if indice < len(eventos) - 1
                else ""
            )

            st.markdown(
                f"""
                <div class="timeline-marker">
                    <div
                        class="timeline-circle"
                        style="background:
                        {CORES_EVENTOS[evento['tipo']]};
                        "
                    ></div>
                    {linha}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with coluna_conteudo:
            with st.expander(
                (
                    f"{data_label} | "
                    f"{evento['titulo']}"
                )
            ):
                if evento["tipo"] == "SAT":
                    col_math, col_english = (
                        st.columns(2)
                    )

                    col_math.metric(
                        "Math",
                        formatar_resultado(
                            evento["math"]
                        ),
                    )

                    col_english.metric(
                        "English",
                        formatar_resultado(
                            evento["english"]
                        ),
                    )

                else:
                    st.markdown(
                        "**Responsável pelo atendimento**"
                    )

                    st.write(
                        evento["responsavel"]
                        or "Não informado"
                    )

                    st.markdown(
                        "**Tipo de Atendimento**"
                    )

                    st.write(
                        evento["tipo_atendimento"]
                        or "Não informado"
                    )

                    st.markdown(
                        "**Registro do Atendimento**"
                    )

                    st.write(
                        evento["registro"]
                        or "Não informado"
                    )


def renderizar_dash_micro(
    base_alunos,
):
    st.title("Dash Micro")

    aluno = selecionar_aluno(
        base_alunos,
        key="aluno_dash_micro",
    )

    if aluno is None:
        return

    ra = aluno["ra"]

    sats = carregar_sats()
    atendimentos = carregar_atendimentos()
    prep_students = carregar_prep_students()

    linha_sat = obter_linha_por_ra(
        sats,
        ra,
    )

    linha_prep = obter_linha_por_ra(
        prep_students,
        ra,
    )

    col_math, col_english, col_super = (
        st.columns(3)
    )

    col_math.metric(
        "Math max",
        formatar_resultado(
            obter_valor_linha(
                linha_sat,
                ["Math max"],
            )
        ),
    )

    col_english.metric(
        "English max",
        formatar_resultado(
            obter_valor_linha(
                linha_sat,
                ["English max"],
            )
        ),
    )

    col_super.metric(
        "Superscore",
        formatar_resultado(
            obter_valor_linha(
                linha_sat,
                ["Superscore"],
            )
        ),
    )

    renderizar_informacoes_prep(
        linha_prep
    )

    eventos = (
        construir_eventos_atendimentos(
            atendimentos,
            ra,
        )
        + construir_eventos_sat(
            linha_sat
        )
    )

    renderizar_timeline(
        eventos
    )


# =========================================================
# ROTEAMENTO
# =========================================================
def renderizar_conteudo(
    base_alunos,
):
    pagina = st.session_state[
        "pagina_atual"
    ]

    if pagina == "Indicadores Application":
        renderizar_pagina_indicadores(
            base_alunos,
            "Application",
        )

    elif pagina == "Status Application":
        renderizar_status_application(
            base_alunos
        )

    elif pagina == "Indicadores Pre-Application":
        renderizar_pagina_indicadores(
            base_alunos,
            "Pre-Application",
        )

    elif pagina == "Dash Micro":
        renderizar_dash_micro(
            base_alunos
        )

    elif pagina == "Registro de Atendimento":
        renderizar_registro_atendimento(
            base_alunos
        )

    else:
        st.title("Administrativo")

        st.info(
            "Funcionalidades administrativas "
            "serão incluídas posteriormente."
        )


def main():
    aplicar_estilos()
    inicializar_navegacao()

    try:
        base_alunos = (
            carregar_base_alunos_ativos()
        )

    except Exception as error:
        st.error(
            f"Erro ao carregar BASE_ALUNOS: {error}"
        )
        st.stop()

    base_filtrada = renderizar_sidebar(
        base_alunos
    )

    renderizar_conteudo(
        base_filtrada
    )


if __name__ == "__main__":
    main()