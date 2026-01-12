"""
Author: Tjalf Caesar (655646)
Date: 2025-01-06
Description: This preprocessing model has been trained on the following dataset: EEG Motor Movement/Imagery Dataset.
"""

from tkinter import FIRST
import mne
from scipy.sparse import data
import data_loader
from logger import Logger
import torch
import torch.optim as optim
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from general_plotting import plot_noisy_vs_denoised
from denosing_network import DenoisingAutoencoderModule


# Logging configuration
LOG_DIRECTORY = "logs"
LOG_FILE = "preprocessing.log"
OUTPUT_DIRECTORY_TOOLS = "preprocessed_tools"
OUTPUT_DIRECTORY_NETWORK = "preprocessed_network"


# Create a Logger instance
app_logger = Logger(log_dir=LOG_DIRECTORY, log_file=LOG_FILE).get_logger()


def set_montage(raw):
    """
    Sets a custom montage for the raw EEG data.

    Parameters:
        raw (mne.io.Raw): The raw EEG data to update.
    """
    app_logger.info("Setting custom montage for raw data.")
    try:
        available_channels = [
            "Fc5.",
            "Fc3.",
            "Fc1.",
            "Fcz.",
            "Fc2.",
            "Fc4.",
            "Fc6.",
            "C5..",
            "C3..",
            "C1..",
            "Cz..",
            "C2..",
            "C4..",
            "C6..",
            "Cp5.",
            "Cp3.",
            "Cp1.",
            "Cpz.",
            "Cp2.",
            "Cp4.",
            "Cp6.",
            "Fp1.",
            "Fpz.",
            "Fp2.",
            "Af7.",
            "Af3.",
            "Afz.",
            "Af4.",
            "Af8.",
            "F7..",
            "F5..",
            "F3..",
            "F1..",
            "Fz..",
            "F2..",
            "F4..",
            "F6..",
            "F8..",
            "Ft7.",
            "Ft8.",
            "T7..",
            "T8..",
            "T9..",
            "T10.",
            "Tp7.",
            "Tp8.",
            "P7..",
            "P5..",
            "P3..",
            "P1..",
            "Pz..",
            "P2..",
            "P4..",
            "P6..",
            "P8..",
            "Po7.",
            "Po3.",
            "Poz.",
            "Po4.",
            "Po8.",
            "O1..",
            "Oz..",
            "O2..",
            "Iz..",
        ]

        channel_positions = {
            channel: [i, i + 0.1, i + 0.2]
            for i, channel in enumerate(available_channels)
        }
        montage = mne.channels.make_dig_montage(
            ch_pos=channel_positions, coord_frame="head"
        )
        raw.set_montage(montage, on_missing="ignore")
        app_logger.info("Montage set successfully.")
    except Exception as e:
        app_logger.error(f"Error setting montage: {e}")
        raise




def perform_preprocessing(raw_dictionary):
    app_logger.info("Starting preprocessing by preprocessing tools.")
    preprocessed_data_dictionary = {}

    # Import the EEGPreprocessing class
    from preprocessing_tools import EEGPreprocessingTools

    preprocessing_tools = EEGPreprocessingTools(logger=app_logger)

    band_passed_choice = input("Bandpass filter: [y/n]: ").strip()
    ica_choice = input("Apply ica: [y/n]: ").strip()

    # Prompt user for decision
    print("Select reference method:")
    print("1. Use centre of the brain")
    print("2. Use common average")
    print("n. Skip reference setting")

    reference_choice = input("Set reference channel: [1/2/n]: ").strip()

    # Choose epochs creating method
    print("Select epochs creating method:")
    print("1. Create epochs dictionary without any further processing")
    print("2. Create epochs dictionary with baseline middling")
    print("n. Skip epochs creation")

    epochs_choice = input("Creating epochs_choice: [1/2/n]: ").strip()

    # Flag to indicate if it's the first subject
    first_subject = True 

    # Tors the data for the first subject for plotting
    noisy_data = None

    for subject in raw_dictionary:
        if first_subject:
            noisy_data=raw_dictionary[subject].get_data()

        app_logger.info(f"Start preprocessing for subject {subject}.")
        raw = raw_dictionary[subject]

        set_montage(raw)

        if band_passed_choice == "y":
            app_logger.info("Applying bandpass filter.")
            raw = preprocessing_tools.band_filter(raw, 8.0, 12.0, 18.0, 26.0)
        elif band_passed_choice == "n":
            app_logger.info("Skipping bandpass filter by choice.")

        else:
            app_logger.error("Invalid choice. Skipping bandpass filter.")

        if ica_choice == "y":
            app_logger.info("Applying ica.")
            raw = preprocessing_tools.apply_ica(raw)
        elif ica_choice == "n":
            app_logger.info("Skipping ica by choice.")

        else:
            app_logger.error("Invalid choice. Skipping ica.")

        if reference_choice == 1:
            app_logger.info("Using centre of the brain.")
            raw = preprocessing_tools.set_reference_channel(raw, ["Cz.."])

        elif reference_choice == 2:
            app_logger.info("Using common average.")
            raw = preprocessing_tools.set_common_average_as_reference(raw)

        elif reference_choice == "n":
            app_logger.info("Skipping referencing.")

        else:
            app_logger.error("Invalid choice. Skipping referencing.")

        preprocessed_data_dictionary[subject] = raw

        # Initialize the EpochsExtractor with the logger
        from epochs_extractor import EpochsExtractor

        epochs_extractor = EpochsExtractor(app_logger)

        if epochs_choice == 1:
            app_logger.info("creating epochs dictionary without any further processin.")
            epochs = epochs_extractor.create_epochs_dictionary(
                preprocessed_data_dictionary, -1.0, 4.0
            )

        elif epochs_choice == 2:
            app_logger.info("Creating epochs dictionary with baseline middling.")
            epochs = epochs_extractor.create_epochs_dictionary(
                preprocessed_data_dictionary, -1.0, 4.0
            )

        elif epochs_choice == "n":
            app_logger.info("Skipping epochs creation by choice.")

        else:
            app_logger.error("Invalid choice. Skipping epochs creation.")

         # Plot only for the first subject for presentation purposes.
        if first_subject:
            plot_noisy_vs_denoised(noisy_data, raw.get_data(), subject)

            first_subject = False  # Set flag to False after plotting for the first subject
            app_logger.info("Plotted first subject")
           
            # epochs = epochs_extractor.create_epochs_dictionary(preprocessed_data_dictionary, -1.0, 4.0)
        epochs = epochs_extractor.baseline_middling(
            preprocessed_data_dictionary, -1.0, 4.0
        )
        app_logger.info(f"Created epochs FreigabecompletSmartcompleteed.")

    epochs_extractor.store_preprocessed_to_file(epochs, OUTPUT_DIRECTORY_TOOLS)
    app_logger.info("Storing epochs to file completed.")




def main():
    """
    The main function with dynamic decision-making over the console.
    """
    app_logger.info("Starting preprocessing script.")

    try:

        # Choose epochs creating method
        print("Select mode:")
        print("1. Debugging")
        print("2. Production")
        mode_choice = input("Set mode: [1/2]: ").strip()

        # Load raw EEG data
        from data_loader import DataLoader

        data_loader = DataLoader(app_logger)

        if mode_choice == "1":
            app_logger.info("Using debugging mode.")
            raw_dictionary = data_loader.load_data_from_list(
                [1, 2, 3, 4], [1, 2, 3, 4, 7, 8, 11, 12]
            )

        elif mode_choice == "2":
            app_logger.info("Starting production mode.")
            # Load the whole dataset.
            raw_dictionary = data_loader.load_all([1, 2, 3, 4, 7, 8, 11, 12])

        else:
            app_logger.error(f"Invalid choice: {mode_choice}. Exit program.")
            return

        # Prompt user for decision
        print("Select preprocessing method:")
        print("1. Use Denoising Network")
        print("2. Use Preprocessing Tools")

        choice = input("Enter your choice (1 or 2): ").strip()

        if choice == "1":
            app_logger.info("Using denoising network for preprocessing.")
            preprocessed_data_dictionary = use_denoising_network(
                raw_dictionary, mode_choice
            )
        elif choice == "2":
            app_logger.info("Using preprocessing tools for preprocessing.")
            preprocessed_data_dictionary = use_preprocessing_tools(raw_dictionary)
        else:
            app_logger.error("Invalid choice. Exiting the script.")
            print(
                "Invalid choice. Please restart the script and select a valid option."
            )
            return

        app_logger.info("Preprocessing completed successfully.")

    except Exception as e:
        app_logger.error(f"Error during preprocessing: {e}")
        raise


if __name__ == "__main__":
    main()