import simpy
import random
import pandas as pd

class g:
    # Inter-arrival times
    patient_inter = 10
    call_inter = 5

    # Activity times
    mean_reg_time = 2
    mean_gp_time = 8
    mean_book_test_time = 4
    mean_call_time = 4

    # Resource numbers
    number_of_receptionists = 1
    number_of_gps = 2

    # Branch probabilities
    prob_book_test = 0.25

    # Simulation meta parameters
    sim_duration =450
    number_of_runs = 10

# Class representing patients coming in to the GP surgery
class Patient:
    def __init__(self, p_id):
        self.id = p_id
        self.arrival_time = 0
        self.q_time_reg = 0
        self.q_time_gp = 0
        self.time_with_gp = 0
        self.q_time_book_test = 0
        self.time_with_receptionist = 0.0

# Class representing callers phoning the GP surgery
class Caller:
    def __init__(self, c_id):
        self.id = c_id
        self.call_time = 0
        self.time_with_receptionist = 0.0
        self.q_time_call = 0

# Class representing our model of the GP surgery
class Model:
    # Constructor
    def __init__(self, run_number):
        # Set up SimPy environment
        self.env = simpy.Environment()

        # Set up counters to use as entity IDs
        self.patient_counter = 0
        self.caller_counter = 0

        # Set up lists to store patient objects
        self.patient_objects = [] ##NEW
        self.caller_objects = [] ##NEW

        # Set up resources
        self.receptionist = simpy.Resource(
            self.env, capacity=g.number_of_receptionists
        )
        self.gp = simpy.Resource(
            self.env, capacity=g.number_of_gps
        )

        # Set run number from value passed in
        self.run_number = run_number

        # Set up DataFrame to store patient-level results
        self.patient_results_df = pd.DataFrame()
        self.patient_results_df["Patient ID"] = [1]
        self.patient_results_df["Arrival Time"] = [0.0]
        self.patient_results_df["Queue Time Reg"] = [0.0]
        self.patient_results_df["Time Seen For Registration"] = [0.0]
        self.patient_results_df["Queue Time GP"] = [0.0]
        self.patient_results_df["Time Seen By GP"] = [0.0]
        self.patient_results_df["Queue Time Book Test"] = [0.0]
        self.patient_results_df["Time Test Booking Started"] = [0.0]
        self.patient_results_df["Departure Time"] = [0.0]
        self.patient_results_df.set_index("Patient ID", inplace=True)

        # Set up DataFrame to store caller-level results
        self.caller_results_df = pd.DataFrame()
        self.caller_results_df["Caller ID"] = [1]
        self.caller_results_df["Call Start Time"] = [0.0]
        self.caller_results_df["Queue Time Call"] = [0.0]
        self.caller_results_df["Call Answered At"] = [0.0]
        self.caller_results_df["Call End Time"] = [0.0]
        self.caller_results_df.set_index("Caller ID", inplace=True)

        # Set up attributes that will store mean queuing times across the run
        self.mean_q_time_reg = 0
        self.mean_q_time_gp = 0
        self.mean_q_time_book_test = 0
        self.mean_q_time_call = 0

        # Set up attributes used to monitor total resource usage
        self.receptionist_utilisation_prop = 0.0
        self.gp_utilisation_prop = 0.0

    # Generator function that represents the DES generator for patient arrivals
    def generator_patient_arrivals(self):
        while True:
            self.patient_counter += 1

            p = Patient(self.patient_counter)
            self.patient_objects.append(p) ##NEW

            self.env.process(self.attend_gp_surgery(p))

            sampled_inter = random.expovariate(1.0 / g.patient_inter)

            yield self.env.timeout(sampled_inter)

    # Generator function that represents the DES generator for caller arrivals
    def generator_callers(self):
        while True:
            self.caller_counter += 1

            c = Caller(self.caller_counter)
            self.caller_objects.append(c) ##NEW

            self.env.process(self.call_gp_surgery(c))

            sampled_inter = random.expovariate(1.0 / g.call_inter)

            yield self.env.timeout(sampled_inter)

    # Generator function representing pathway for patients attending the GP
    # surgery to see a GP
    def attend_gp_surgery(self, patient):
        # Registration activity
        start_q_reg = self.env.now
        self.patient_results_df.at[patient.id, "Arrival Time"] = (
                start_q_reg
            )

        with self.receptionist.request() as req:
            yield req

            end_q_reg = self.env.now

            patient.q_time_reg = end_q_reg - start_q_reg

            self.patient_results_df.at[patient.id, "Queue Time Reg"] = (
                patient.q_time_reg
            )
            self.patient_results_df.at[patient.id, "Time Seen For Registration"] = (
                start_q_reg + patient.q_time_reg
            )

            sampled_reg_time = random.expovariate(
                1.0 / g.mean_reg_time
            )

            patient.time_with_receptionist += sampled_reg_time

            yield self.env.timeout(sampled_reg_time)

        # GP Consultation activity
        start_q_gp = self.env.now

        with self.gp.request() as req:
            yield req

            end_q_gp = self.env.now

            patient.q_time_gp = end_q_gp - start_q_gp

            self.patient_results_df.at[patient.id, "Queue Time GP"] = (
                patient.q_time_gp
            )
            self.patient_results_df.at[patient.id, "Time Seen By GP"] = (
                start_q_gp + patient.q_time_gp
            )

            sampled_gp_time = random.expovariate(
                1.0 / g.mean_gp_time
            )

            patient.time_with_gp += sampled_gp_time

            yield self.env.timeout(sampled_gp_time)

        # Branching path check to see if patient needs to book a test
        if random.uniform(0,1) < g.prob_book_test:
            # Book test activity
            start_q_book_test = self.env.now

            with self.receptionist.request() as req:
                yield req

                end_q_book_test = self.env.now

                patient.q_time_book_test = end_q_book_test - start_q_book_test

                self.patient_results_df.at[patient.id, "Queue Time Book Test"] = (
                    patient.q_time_book_test
                )

                self.patient_results_df.at[patient.id, "Time Test Booking Started"] = (
                    start_q_book_test + patient.q_time_book_test
                )

                sampled_book_test_time = random.expovariate(
                    1.0 / g.mean_book_test_time
                )

                patient.time_with_receptionist += sampled_book_test_time

                yield self.env.timeout(sampled_book_test_time)

            self.patient_results_df.at[patient.id, "Departure Time"] = (
                self.env.now
            )

    # Generator function representing callers phoning the GP surgery
    def call_gp_surgery(self, caller):
        # Answering call activity
        start_q_call = self.env.now
        self.caller_results_df.at[caller.id, "Call Start Time"] = (
                start_q_call
            )

        with self.receptionist.request() as req:
            yield req

            end_q_call = self.env.now

            caller.q_time_call = end_q_call - start_q_call

            self.caller_results_df.at[caller.id, "Queue Time Call"] = (
                caller.q_time_call
            )

            self.caller_results_df.at[caller.id, "Call Answered At"] = (
                self.env.now
            )

            sampled_call_time = random.expovariate(
                1.0 / g.mean_call_time
            )

            caller.time_with_receptionist += sampled_call_time

            yield self.env.timeout(sampled_call_time)

            self.caller_results_df.at[caller.id, "Call End Time"] = (
                self.env.now
            )

    # Method to calculate and store results over the run
    def calculate_run_results(self):
        self.mean_q_time_reg = self.patient_results_df["Queue Time Reg"].mean()
        self.mean_q_time_gp = self.patient_results_df["Queue Time GP"].mean()
        self.mean_q_time_book_test = (
            self.patient_results_df["Queue Time Book Test"].mean()
        )

        self.mean_q_time_call = self.caller_results_df["Queue Time Call"].mean()

        gp_utilisation_mins = sum([i.time_with_gp for i in self.patient_objects])

        receptionist_utilisation_mins = sum(
            [i.time_with_receptionist for i in self.patient_objects]
            ) + sum(
            [i.time_with_receptionist for i in self.caller_objects]
            )

        self.gp_utilisation_prop = (
            gp_utilisation_mins / (g.number_of_gps * g.sim_duration)
            )

        self.receptionist_utilisation_prop = (
            receptionist_utilisation_mins / (g.number_of_receptionists * g.sim_duration)
        )


    # Method to run a single run of the simulation
    def run(self):
        # Start up DES generators
        self.env.process(self.generator_patient_arrivals())
        self.env.process(self.generator_callers())

        # Run for the duration specified in g class
        self.env.run(until=g.sim_duration)

        # Calculate results over the run
        self.calculate_run_results()

        return self.caller_results_df, self.patient_results_df

# Class representing a trial for our simulation
class Trial:
    # Constructor
    def __init__(self):
        self.df_trial_results = pd.DataFrame()
        self.df_trial_results["Run Number"] = [1]
        self.df_trial_results["Mean Queue Time Reg"] = [0.0]
        self.df_trial_results["Mean Queue Time GP"] = [0.0]
        self.df_trial_results["Mean Queue Time Book Test"] = [0.0]
        self.df_trial_results["Mean Queue Time Call"] = [0.0]
        self.df_trial_results["GP Utilisation - Percentage"] = [0.0]
        self.df_trial_results["Receptionist Utilisation - Percentage"] = [0.0]
        self.df_trial_results.set_index("Run Number", inplace=True)

    # Method to calculate and store means across runs in the trial
    def calculate_means_over_trial(self):
        self.mean_q_time_reg_trial = (
            self.df_trial_results["Mean Queue Time Reg"].mean()
        )
        self.mean_q_time_gp_trial = (
            self.df_trial_results["Mean Queue Time GP"].mean()
        )
        self.mean_q_time_book_test_trial = (
            self.df_trial_results["Mean Queue Time Book Test"].mean()
        )
        self.mean_q_time_call_trial = (
            self.df_trial_results["Mean Queue Time Call"].mean()
        )

    # Method to run trial
    def run_trial(self):
        caller_dfs = []
        patient_dfs = []

        for run in range(1, g.number_of_runs+1):
            my_model = Model(run)
            caller_df, patient_df = my_model.run()
            caller_df["Run"] = run
            caller_df["What"] = "Callers"
            patient_df["Run"] = run
            patient_df["What"] = "Patients"

            caller_dfs.append(caller_df)
            patient_dfs.append(patient_df)

            self.df_trial_results.loc[run] = [my_model.mean_q_time_reg,
                                              my_model.mean_q_time_gp,
                                              my_model.mean_q_time_book_test,
                                              my_model.mean_q_time_call,
                                              round(my_model.gp_utilisation_prop * 100, 2),
                                              round(my_model.receptionist_utilisation_prop*100, 2)
                                              ]

        return self.df_trial_results.round(1), pd.concat(caller_dfs), pd.concat(patient_dfs)
