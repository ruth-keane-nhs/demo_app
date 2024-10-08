import simpy
import random
import pandas as pd
import numpy as np
import plotly.express as px
import re
import streamlit as st
from des_classes import g, Trial

st.title("DES example")
button_run_pressed = st.button("Run simulation")



with st.sidebar:
    patient_inter_input = st.slider("Select the time between patient arrivals", min_value=0, max_value=20, value= 3)
    call_inter_input = st.slider("Select the time between calls", min_value= 0, max_value=30,value= 10)
    sim_duration_input = st.number_input("""Select the duration of the :green[simulation] 
                                         (**Maximum value is 2000**)""", 
                                         min_value=60, max_value=2000, value=480)


g.patient_inter = patient_inter_input
g.call_inter = call_inter_input
g.sim_duration = sim_duration_input

tab1, tab2 = st.tabs(["summary results","extra graphs"])

with tab1:
    st.write("hello")
    

###########################################################
# Run a trial using the parameters from the g class and   #
# print the results                                       #
###########################################################
if button_run_pressed:
    with st.spinner("Running simulation"):

        df_trial_results, caller_results, patient_results = Trial().run_trial()

        # #print(df_trial_results)

        # #print(caller_results.sample(25))

        # #print(patient_results.sample(25))

        # #print("=== Receptionist Stats ===")

        # #print(f"The median wait for registration across {g.number_of_runs} " +
        #       f"was {df_trial_results['Mean Queue Time Reg'].median():.1f} minutes")

        # print(f"The median wait for booking a test " +
        #       f"was {df_trial_results['Mean Queue Time Book Test'].median():.1f} minutes")

        # print(f"The median wait for callers to have their call answered " +
        #       f"was {df_trial_results['Mean Queue Time Call'].median():.1f} minutes")

        # print(f"The median utilisation for a receptionist across {g.number_of_runs} " +
        #       f"was {df_trial_results['Receptionist Utilisation - Percentage'].median()}%")

        # print("=== GP Stats ===")

        # print(f"The median wait for a GP across {g.number_of_runs} " +
        #       f"was {df_trial_results['Mean Queue Time GP'].median():.1f} minutes")


        # print(f"The median utilisation for a GP across {g.number_of_runs} " +
        #       f"was {df_trial_results['GP Utilisation - Percentage'].median()}%")

        ###########################################################
        ###########################################################
        # Create some summaries and visualisations for averages   #
        # across the trial                                        #
        ###########################################################
        ###########################################################

        with tab2:
            # Let's set up a reusable sequence of colours that can give our plotly plots a consistent
            # feel/identity
            # This uses some colours from the NHS identity guidelines that should work well when
            # placed next to each other
            # https://www.england.nhs.uk/nhsidentity/identity-guidelines/colours/
            # If we pass this to something with just a single colour in the plot, it will just take the
            # first colour from the sequence (NHS Blue)
            # If we pass it to a plot that has categories, it will assign colours to categories
            # in the order given in this list
            nhs_colour_sequence = ["#005EB8", "#FFB81C", "#00A499", "#41B6E6", "#AE2573", "#006747"]

            ##############################################
            # Bar plot - average waits per stage per run #
            ##############################################
            average_waits_fig = px.bar(
                # First we need to get the dataframe into the shape needed by the plot
                # We start by dropping the utilisation columns from our dataframe
                # as they're on a very different scale to the wait times
                df_trial_results.drop(
                    columns=["GP Utilisation - Percentage",
                            "Receptionist Utilisation - Percentage"])
                            # We then reset the index of the plot so the run number is
                            # a column rather than the index of the dataframe
                            .reset_index(drop=False)
                            # Finally, we use the melt function to turn this from a 'wide'
                            # dataframe (where we have a column for each of the different measures)
                            # to a 'long' dataframe where we have one row per run/metric combination.
                            # After melting, our original column names will be in a column entitled
                            # 'variable' and our actual wait times for each stage will be in a column
                            # # called 'value'
                            # (so a row might look like "1, Mean Queue Time Reg, 87" for the 'Run Number',
                            # 'variable' and 'value' columns respectively)
                            .melt(id_vars="Run Number"),
                    x="value", # What's on the horizontal axis - this is the number of minutes
                    y="Run Number", # What's on the vertical axis
                    facet_col="variable", # This will create a separate plot for each variable (here, the metric)
                    # Give the whole plot a title
                    title="Average Waits (Minutes) For Each Stage of the Patient Journey - by Run",
                    orientation='h', # Set this to a horizontal bar plot (default is vertical)
                    labels={"value": "Average Wait (Mins)"}, # Make the label on the x axis nicer
                    # Use our NHS colour palette; only the first colour will be used as we haven't
                    # made use of colour as a part of the visualisation in this plot, but this does mean
                    # that the bars will use the standard NHS blue rather than the plotly one
                    color_discrete_sequence=nhs_colour_sequence
                    )

            # After we use the px.bar function to create our plot, there will be a few additional things
            # we want to do to the plot before displaying it. There is a limit to what can be done in
            # the original function call as there are only so many parameters - these little extra touches
            # just make the plot as readable and polished-looking as possible!

            # This will tidy up the subtitles of each 'facet' within our plot (the mini-graph relating)
            # to each of our metrics
            # This uses what's called a 'lambda' function, which is a little temporary function that in this case
            # iterates through the annotation text and replaces the string 'variable=' with an empty string,
            # which just tidies up the headers in this case so it only contains the actual name of the variable
            average_waits_fig.for_each_annotation(lambda a: a.update(text=a.text.replace("variable=", "")))

            # Here we are going to update the layout to ensure that we have a label for every run number in
            # our y axis
            # By default, plotly tries to intelligently choose a scale - but for this, it makes more sense to
            # include a label for every row (unless we have lots of runs, in which case we won't apply this
            # correction)
            if g.number_of_runs < 20:
                average_waits_fig.update_layout(yaxis = {'dtick': 1})

            # Finally, we force plotly to display the plot in the interactive window.
            # If we don't use this then only the final plotly plot we create will actually be displayed
            #average_waits_fig.show()
            st.plotly_chart(average_waits_fig)
            ##############################################
            # Bar plot - waits per stage per run         #
            ##############################################

            performance_per_run_fig = px.bar(
                # First we need to get the dataframe into the shape needed by the plot
                # We start by dropping the utilisation columns from our dataframe
                # as they're on a very different scale to the wait times
                df_trial_results.drop(
                    columns=["GP Utilisation - Percentage",
                            "Receptionist Utilisation - Percentage"])
                            # We then reset the index of the plot so the run number is
                            # a column rather than the index of the dataframe
                            .reset_index(drop=False)
                            # This time we use a lambda function (a small temporary function)
                            # to look at each of our column names and replace the string
                            # 'Mean Queue Time ' with a blank string, which we want to do here
                            # as we're going to use those values as our x axis labels and it will
                            # get cluttered and hard to read with that phrase used (and we can just make
                            # it clear what each value is via other labels or the title)
                            .rename(columns=lambda x: re.sub('Mean Queue Time ', '', x))
                            # Finally, we reshape the dataframe from a wide to a long format
                            # (see the first plot for more details on this)
                            .melt(id_vars="Run Number"),
                # This time we're going to facet (make mini sub-plots) by run instead - we're aiming to
                # end up with a mini-plot per run to look at the performance on a run level rather than
                # in the previous plot where we had more ability to look at the performance against a
                # single metric across multiple runs - so even though we're using the same data here,
                # the focus of the plot is slightly different
                facet_col="Run Number",
                facet_col_wrap=10, # Ensure that if we have lots of runs, our subplots don't become too small
                x="variable", # the column used for our horizontal axis
                y="value", # the column used for our vertical axis
                # A title for the whole plot
                title="Average Waits (Minutes) For Each Stage of the Patient Journey - by Run",
                # Make use of our NHS colour scheme (again, as this plot will only use a single colour, it just
                # uses the first colour from the list which is the NHS blue)
                color_discrete_sequence=nhs_colour_sequence,
                # Finally we tidy up the labels, replacing 'variable' with a blank string (as it's very clear
                # from the category labels and the other labels on the plot what is displayed there
                labels={"variable": "",
                        "value": "Queue Time (minutes)"
                        })

            # We cycle through and tidy up the display of the subheaders for the subplots
            performance_per_run_fig.for_each_annotation(
                lambda a: a.update(text=a.text.replace("Run Number=", "Run "))
                )

            # This time, as we have multiple x axes in the overall plot (one per subplot) we need to use a
            # slightly different function to ensure every label will get displayed
            performance_per_run_fig.for_each_xaxis(lambda xaxis: xaxis.update(dtick=1))

            # Display the plot
            #performance_per_run_fig.show()
            st.plotly_chart(performance_per_run_fig)
            ###############################################
            # Box plot - resource utilisation by resource #
            ###############################################

            utilisation_boxplot_fig = px.box(
                # First we need to get the dataframe into the shape needed by the plot
                # We start by only selecting the utilisation columns by passing a list of
                # the column names inside another set of square brackets
                (df_trial_results[["GP Utilisation - Percentage",
                            "Receptionist Utilisation - Percentage"]]
                            # once again we want the run number to be a column, not the index
                            .reset_index(drop=False)
                            # and once again we want it in long format (see the first plot for details)
                            .melt(id_vars="Run Number")),
                x="value", # Make our horizontal axis display the % utilisation of the resource in the run
                y="variable", # Make the y axis the utilisation category (will be our original column names)
                points="all", # Force the boxplot to actually show the individual points too, not just a summary
                title="Resource Utilisation", # Add a plot title
                # Force the plot to start at 0 regardless of the lowest utilisation recorded
                # and finish just past 100 so that the higher points can be seen
                range_x=[0, 105],
                # Again, use our NHS colour paletted - this will just use NHS blue (the first colour in the list)
                color_discrete_sequence=nhs_colour_sequence,
                # Tidy up the x and y axis labels
                labels={"variable": "",
                        "value": "Resource Utilisation Across Run (%)"
                        }
            )

            # We don't need to do any additional tweaks to the plot this time - we can just display it
            # straight away
            #utilisation_boxplot_fig.show()
            st.plotly_chart(utilisation_boxplot_fig)
            ##############################################
            # Bar plot - resource utilisation per run    #
            ##############################################

            # We're going to use the same data as for our boxplot, but we're more interested in looking
            # at the utilisation of resources within a single run rather than the consistency of resource
            # use of a particular resource type, which the boxplot is better at demonstrating
            # So once again - same data, different focus!
            utilisation_bar_fig = px.bar(
                # First we need to get the dataframe into the shape needed by the plot
                # We start by only selecting the utilisation columns by passing a list of
                # the column names inside another set of square brackets
                (df_trial_results[["GP Utilisation - Percentage",
                            "Receptionist Utilisation - Percentage"]]
                            # once again we want the run number to be a column, not the index
                            .reset_index(drop=False)
                            # and once again we want it in long format (see the first plot for details)
                            .melt(id_vars="Run Number")),
                x="Run Number", # The value for our horizontal plot
                y="value", # What will be displayed on the vertical axis (here, utilisation %)
                # This will colour the bars by a factor
                # Here, because we melted our dataframe into long format, the values of the column 'variable'
                # are the names of our original columns - i.e. "GP Utilisation - Percentage" or
                # "Receptionist Utilisation - Percentage". We will automatically get a legend thanks to plotly.
                color="variable",
                # Force the bars to display side-by-side instead of on top of each other (which wouldn't really
                # make sense in this graph)
                barmode="group",
                # Use our NHS colour palette - this time as we have two possible values in the column we coloured
                # by, it will use the first two values in the colour palette (NHS blue and NHS warm yellow)
                color_discrete_sequence=nhs_colour_sequence,
                title="Resource Utilisation",
                labels={"variable": "", # Remove the legend header - it's clear enough without it
                        "value": "Resource Utilisation Across Run (%)" # tidy up our y-axis label
                        }
            )

            # Ensure the run label appears on the x axis for each run unless there are lots of them, in
            # which case we'll just leave the value of dtick as the default (which means plotly will choose
            # a sensible value for us)
            if g.number_of_runs < 20:
                utilisation_bar_fig.update_layout(xaxis = {'dtick': 1})

            # Show the bar plot
            #utilisation_bar_fig.show()
            st.plotly_chart(utilisation_bar_fig)
            ##############################################################
            ###########################################################
            # Create some summaries and visualisations for call stats #
            ###########################################################
            ##############################################################

            ##############################################
            # Dataframe - Call Answering Stats           #
            ##############################################

            # It would be good to be able to display whether callers had their call answered or not - this
            # can give us a quick overview of whether the system has been particularly overloaded on different
            # runs. If a large number of callers never get their call answered, this suggests we need more
            # receptionists (as they are the ones dealing will registration, test booking and calls in
            # this model)

            # Adds a column for whether the call was answered
            # We use np.where as a bit of an 'if'/'case when' statement here
            caller_results["Call Answered"] = np.where(
                # First, we check a condition - is the value in the 'call answered at' column
                # NA/missing?
                caller_results["Call Answered At"].isna(),
                # If it is, then it means we never recorded a 'call answered at' time because a receptionist
                # resource never became free for this caller - so return the string below
                "Call Not Answered Before Closing Time",
                # If it is not na (i.e. the method .isna() returns False), then we can be confident that the
                # call was answered
                "Call Answered"
                )

            # Now let's group by run, keep just our new 'call answered' column, and count how many calls per run
            # fell into each of these categories.
            # As the 'value_counts()' method returns a pandas series instead of a pandas dataframe, we need to
            # manually turn it back into a dataframe first
            calls_answered_df = pd.DataFrame(
                caller_results.groupby("Run")["Call Answered"].value_counts()
            # Finally, we reset the index (as due to grouping by 'Run' that will have been the index of
            # the new column we created, but for plotting and pivoting purposes it's easier if that's an
            # actual column instead)
            ).reset_index(drop=False)

            # For display purposes, it would actually be easier to read if our dataframe was in 'wide' format -
            # which will mean that we have a column for 'call answered by closing time' and a column for
            # 'call not answered before closing time' and a row per run, with the cells then containing
            # the count of calls per run falling into each of those categories
            # We use the 'pivot' function for going from long to wide format
            calls_answered_df_wide = calls_answered_df.pivot(
                index="Run", columns="Call Answered", values="count"
                ).reset_index(drop=False)

            # Finally, let's display this dataframe
            print(calls_answered_df_wide)

            ##########################################################################
            # Stacked Bar Plot - Percentage of Calls Answered - by run              #
            ##########################################################################

            # We can now use the long version of this dataframe to create a stacked bar plot
            # exploring the total number of calls received - and those not answered - within
            # the plot
            calls_answered_fig = px.bar(
                # we can just pass in our 'call_answered_df' without further modification
                calls_answered_df,
                x="Run", # The run should be the x axis
                y="count", # The number of calls falling into each category should by the y axis
                color="Call Answered", # This time we colour the dataframe by whether the call was answered or not
                # Tidy up the y axis label (x axis label and legend title are already fine)
                labels={"count": "Number of Calls"},
                # Pass in our colour sequence - the first category alphabetically will use colour 1,
                # and the second category will use colour 2. If we had more categories, it would continue to
                # make its way through the list of colours we defined
                color_discrete_sequence=nhs_colour_sequence,
                # Add a plot title
                title="Number of Calls - How Many Were Answered in Opening Hours?"
            )

            # Ensure each column has a number on the x axis (if there aren't too many runs)
            if g.number_of_runs < 20:
                calls_answered_fig.update_layout(xaxis = {'dtick': 1})

            # Show the plot
            #calls_answered_fig.show()
            st.plotly_chart(calls_answered_fig)
            ##############################################
            # Strip Plot - Arrival Patterns              #
            ##############################################

            # Finally, let's make a scatterplot that can help us to just check that the patterns of arrivals
            # across the day makes sense. Are the callers and patients arriving in an intermingled fashion
            # and do we have some of each?
            # This plot might be of more use for debugging than actually understanding the model behaviour -
            # although it can also be useful to demonstrate that the arrival times are not fixed across
            # the different runs, which can help people to understand the value and functioning of the model

            # We start by joining the patient and caller results together
            calls_and_patients = pd.concat([
                    # we only want a few columns from each
                    patient_results[["Run", "Arrival Time", "What"]],
                    # It's important that the columns are in the same order and have the same names
                    # as we are just going to stack them on top of each other
                    caller_results[["Run", "Call Start Time", "What"]].rename(columns={"Call Start Time": "Arrival Time"})
                    ])

            # Here we are going to use something called a strip plot, which is a scatterplot (a plot with
            # a series of dots - but with some level of randomness on one axis to ensure points at exactly
            # the same position don't fully overlap)
            arrival_fig = px.strip(
                # We pass in the dataframe we just created
                calls_and_patients,
                # We place the points horizontally depending on the time the individual caller or patient
                # arrived in the model
                x="Arrival Time",
                # We then use the run number on the y axis, which will give us a line of points per run
                y="Run",
                # We'll use the colour to distinguish between patients and callers
                color="What",
                # We'll use our colour palette
                color_discrete_sequence=nhs_colour_sequence,
                # Finally, let's add a title
                title="Patient Arrivals by Time",
                labels={"Arrival Time": "Arrival Time (Simulation Minute)"}
            )

            # Force the maximum amount of jitter (random offset) in the points
            arrival_fig.update_traces(jitter=1.0)

            # Display the plot
            st.plotly_chart(arrival_fig)

            ############################################################
            # Strip Plot - Call Answering by Arrival Time              #
            ############################################################

            # We can also use a similar point to give an indication of at what point our system
            # starts to overload during each run.
            # Instead of displaying both patients and callers, we use just the callers this time
            call_answered_detailed_fig = px.strip(
                # We pass in the dataframe we just created
                caller_results,
                # We place the points horizontally depending on the time the individual caller or patient
                # arrived in the model
                x="Call Start Time",
                # We then use the run number on the y axis, which will give us a line of points per run
                y="Run",
                # We'll use the colour to distinguish between patients and callers
                color="Call Answered",
                # This time, instead of using our palette, let's explicitly map some colours to the possible
                # values
                # This allows us to ensure the 'not answered' gets associated with a typically 'bad' colour
                color_discrete_map={"Call Answered": "#005EB8", # NHS blue
                                    "Call Not Answered Before Closing Time": "#DA291C"}, # NHS Red
                # Finally, let's add a title
                title="Patient Calls - Successful Answering over Time",
                # Make it clearer what the units of the x axis are
                labels={"Call Start Time": "Call Start Time (Simulation Minute)"},
            )

            #call_answered_detailed_fig.show()
            st.plotly_chart(call_answered_detailed_fig)
            ##############################################################
            ##############################################################
            # Create some summaries and visualisations for patient stats #
            ##############################################################
            ##############################################################


            # Not implemented - your code here!
