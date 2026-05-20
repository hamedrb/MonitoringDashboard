import streamlit as st
import pandas as pd

from src.utils.session import invalidate_results, invalidate_report

from src.utils.analysis import generate_metrics, replace_0_by_none_after_closure_date
from src.utils.analysis import generate_stats, generate_subject_counts, compute_end_estimation
from src.utils.analysis import opening_time_alignment, find_inactive_centers, find_last_active_time

from src.utils.plots import generate_barplot, generate_lineplot, generate_donut_plot

from src.utils.report import generate_pdf_report

# ============================================================================================


def load_app() -> None:
    # ========================================================================================
    # File upload

    st.title("📊 Monitoring Dashboard")

    st.header("1. Upload data", divider=True)

    uploaded_excel = st.file_uploader(
        "Upload an Excel file", 
        type=["xlsx", "xls"],
        on_change=invalidate_results
        )

    if uploaded_excel is None:
        st.info("Please upload a file to proceed.",
                icon=":material/info:")
        st.stop()

    # Load data
    with st.spinner("Reading file..."):
        df = pd.read_excel(uploaded_excel)

    # Initialize session states
    if "results_generated" not in st.session_state:
        st.session_state["results_generated"] = False

    if "report_generated" not in st.session_state:
        st.session_state["report_generated"] = False

    # ========================================================================================
    # Display data

    st.header("2. Data Preview", divider=True)

    st.dataframe(df)

    # ========================================================================================
    # Setting

    st.header("3. Settings", divider=True)

    # ====================================
    # Select center column
    st.subheader("A. Centers")

    center_column = st.selectbox(
            "Select the column containing center names",
            df.columns,
            index=None,
            placeholder="Choose column ...",
            on_change=invalidate_results
    )

    if center_column is None:
        st.stop()

    # ====================================
    # Select centers

    available_centers = df[center_column].dropna().unique().tolist()

    selected_centers = st.multiselect(
        'Select centers',
        options=available_centers,
        default=None,
        on_change=invalidate_results
    )

    if len(selected_centers)==0:
        st.stop()
        
    filtered_df = df[df[center_column].isin(selected_centers)].copy()

    # ====================================
    # Select reference date type

    st.subheader("B. Date range")

    date_type = st.radio(
        "Reference date for analysis",
        ["Inclusion date", "Completion date"],
        captions=[
            "Subject enrollment date (first data entry)",
            "Subject closure date (data fully entered)",
        ],
        on_change=invalidate_results
    )

    date_type_key = "inclusion" if date_type == "Inclusion date" else "completion"

    # ====================================
    # Select date column

    date_column = st.selectbox(
        f"Select the column containing {date_type_key} dates",
        filtered_df.columns,
        index=None,
        placeholder="Choose a column...",
        on_change=invalidate_results
    )

    if date_column is None:
        st.stop()

    # Convert to datetime
    filtered_df[date_column] = pd.to_datetime(
        filtered_df[date_column].astype(str), # astype(str) is for not converting numerical columns to date.
        errors='coerce',
        utc=True
    )

    min_date = filtered_df[date_column].min()
    max_date = filtered_df[date_column].max()

    if pd.isna(min_date) or pd.isna(max_date):
        st.error(
            "Selected column does not contain valid dates in format YYYY-MM-DD.",
                icon=":material/error:")
        st.stop()

    # ====================================
    # Select Select date range and aggregation

    col_start, col_end, col_unit = st.columns(3)

    start_date = col_start.date_input("Start date", min_date, on_change=invalidate_results)
    end_date = col_end.date_input("End date", max_date, on_change=invalidate_results)

    time_unit = col_unit.selectbox(
        "Time unit",
        ["Day", "Week", "Month"],
        index=2,
        on_change=invalidate_results
    )

    if start_date > end_date:
        st.error("Start date must be before end date.",
                icon=":material/error:")
        st.stop()

    time_unit_examples = {
        "Day": "2025-09-22", 
        "Week": "2025-09-22/2025-09-28", 
        "Month": "2025-09"
    }

    # ====================================
    # Select time scale

    st.subheader("C. Time scale")

    time_scale = st.radio(
        "Time scale:",
        ["Calendar time", f"Time since first {date_type_key}"],
        captions=[
            f"Displays actual calendar dates (e.g., {time_unit_examples[time_unit]} ...)",
            f"Aligns centers by their first {date_type_key}, displays numerated time periods (e.g. {time_unit} 1 ...)",
        ],
        on_change=invalidate_results
    )

    st.info("This selection affects all time-based analyses and plots.", 
            icon=":material/info:")

    # ====================================
    # Check if a center has been closed and set closure time

    closure_dates = {}

    # Compute counts
    with st.spinner("Computing statistics..."):
        counts_df, centers = generate_subject_counts(
            time_unit, start_date, end_date, 
            filtered_df, center_column, date_column
        )
        
    if counts_df.empty or counts_df[centers].sum().sum()==0:
        st.warning("No data available for selected filters.")
        counts_df = None
        st.stop()

    if "Time since first" in time_scale:
        # 1- Check inactive centers and set closure dates if applicable
        inactive_centers = find_inactive_centers(counts_df, centers)

        if inactive_centers:
            st.subheader("D. Inactive centers validation")
            st.write(f"{len(inactive_centers)} centers found with 0 {date_type_key} in the last period of selected time range:")

            for i, center in enumerate(inactive_centers):
                st.markdown(f"##### {i+1}- {center}")

                is_active = st.radio(
                    f"Is {center} still active?",
                    ["Yes", "No"],
                    key=f"inactive_{center}",
                    on_change=invalidate_results
                )

                if is_active == "No":
                    last_active_ind = find_last_active_time(counts_df[center])
                    closure_date = st.selectbox(
                        f"Select closure time for {center}",
                        counts_df["Time"],
                        index=int(last_active_ind),
                        key=f"closure_{center}",
                        on_change=invalidate_results
                    )

                    # Validation: check if inclusion exists after closure
                    idx = counts_df.index[counts_df["Time"] == closure_date][0]
                    after_values = counts_df.loc[idx:, center]

                    if (after_values > 0).any():
                        st.warning(
                            f"Invalid closure date for {center}: There are inclusions after this date.", 
                            icon=":material/warning:"
                        )
                    else:
                        st.success("Closure date is valid. No activity exists in this center after the selected closure date.",
                                icon=":material/check_circle:"
                                )
                        closure_dates[center] = closure_date

        if closure_dates:
            counts_df = replace_0_by_none_after_closure_date(counts_df, closure_dates)

        # 2- Time alignment of centers
        counts_df = opening_time_alignment(time_unit, counts_df, centers)


    st.divider()

    if st.button("Generate Results", type="primary"):
        st.session_state["results_generated"] = True

    if not st.session_state["results_generated"]:
        st.stop()


    # ========================================================================================
    # Results

    with st.spinner("Generating analyses and visualizations..."):
        st.header("4. Results", divider=True)

        # -----------------------------------
        # Tables

        st.subheader(f"Subject counts per {time_unit.lower()}")
        if "Time since first" in time_scale:
            st.dataframe(counts_df, width='stretch', hide_index=True)
        else:
            st.dataframe(counts_df, width='stretch')

        st.subheader("Statistical measures")
        stats_df = generate_stats(counts_df, centers, time_unit, time_scale)
        st.dataframe(stats_df, width='stretch')

        # -----------------------------------
        # Plots

        st.subheader("Visualizations")
        fig_bar = generate_barplot(counts_df, centers, time_unit)
        st.plotly_chart(fig_bar, config={'width': 'stretch'})

        fig_line = generate_lineplot(counts_df, centers, time_unit)
        st.plotly_chart(fig_line, config={'width': 'stretch'})

        fig_donut = generate_donut_plot(stats_df, centers)
        st.plotly_chart(fig_donut, config={'width': 'stretch'})

        # -----------------------------------
        # Key metrics

        st.subheader(f"Last {time_unit.lower()} activity")

        n_cols = min(len(centers), 2)  # max 2 per row
        rows = [centers[i:i + n_cols] for i in range(0, len(centers), n_cols)]

        for row_centers in rows:
            cols = st.columns(len(row_centers))
            for i, center in enumerate(row_centers):
                current, delta = generate_metrics(counts_df, center, closure_dates)
                cols[i].metric(center, current, delta)

        # ========================================================================================
        # Estimation of last inclusion/closure date

        st.header(f"5. Estimation of Last {date_type_key.capitalize()} Date ", divider=True)

        enable_estimation = st.radio(
            f"Include estimation of last {date_type_key} date?",
            ["Yes", "No"],
            captions=[
                "Estimate based on current recruitment trends per center.",
                "Skip estimation in the report.",
            ],
            index=1,
            on_change=invalidate_report
        )

        # -----------------------------------
        # Show warning
        if enable_estimation=="Yes":
            if pd.Timestamp(start_date, tz="UTC") > min_date:
                st.warning(
                    "The study seems to have started before the selected period.\n\n"
                    "👉 For accurate estimates, set the start date to the beginning of the study.",
                    icon=":material/warning:"
                )

        # -----------------------------------
        # Input expected subjects

        if enable_estimation=="Yes":
            st.subheader("Target subjects per center")
            st.caption("Enter the planned total number of subjects for each center.")

            expected_subjects = {}

            # Better layout (avoid 1 column per center if many)
            n_cols = min(len(centers), 2) # max 2 per row
            rows = [centers[i:i + n_cols] for i in range(0, len(centers), n_cols)]

            for row_centers in rows:
                cols = st.columns(len(row_centers))
                for i, center in enumerate(row_centers):
                    expected_subjects[center] = cols[i].number_input(
                        center,
                        min_value=0,
                        step=1,
                        on_change=invalidate_report
                    )
        else:
            estimation_df = None

        # -----------------------------------
        # Compute estimation

        if enable_estimation=="Yes":
            with st.spinner("Computing estimations..."):
                estimation_df = compute_end_estimation(
                    time_unit,
                    str(min_date),
                    end_date,
                    counts_df, 
                    filtered_df,
                    center_column, 
                    date_column, 
                    centers,
                    expected_subjects
                )
                if estimation_df is not None:
                    st.subheader(f"Estimated last {date_type_key} dates")
                    st.caption(f"Based on the average {date_type_key} rate over the selected time period from {start_date} to {end_date}")
                    st.dataframe(estimation_df, width='stretch')
                    st.caption(f"*Recruited subjects since the beginning of study {min_date}.")

        # -----------------------------------
        # Generate report button

        st.divider()

        if st.button("Generate report", type="primary"):
            st.session_state["report_generated"] = True

        if not st.session_state["report_generated"]:
            st.stop()
    # ========================================================================================
    # Generate report

    with st.spinner("Generating report..."):
        
        hide_index = True if "Time since first" in time_scale else False 

        # Generate report
        pdf_buffer = generate_pdf_report(
            counts_df,
            stats_df,
            centers,
            closure_dates,
            time_unit,
            hide_index,
            fig_bar,
            fig_line,
            fig_donut,
            estimation_df if enable_estimation == "Yes" else None,
            metrics_func=generate_metrics
        )

        st.header(f"6. Download Report ", divider=True)

        # Download button
        st.download_button(
            label="📄 Download Monitoring Report (PDF)",
            data=pdf_buffer,
            file_name="monitoring_report.pdf",
            mime="application/pdf"
        )