import mne
import numpy as np
import logging
import os


class EEGPreprocessingTools:
    """
    Class with a collection of tools for preprocessing EEG data, including functions for ICA, filtering,
    baseline correction, epoch creation, and reference channel setting.
    """

    def __init__(self, logger=None, log_dir="logs", log_file="preprocessing.log"):
        """
        Initializes the EEGPreprocessing class with logging configuration.

        Parameters:
            logger (logging.Logger): Optional logger passed from the main module.
            log_dir (str): Directory for log files.
            log_file (str): Log file name.
        """
        self.log_dir = log_dir
        self.log_file = log_file

        if logger is None:
            # Set up default logging to file and console
            os.makedirs(self.log_dir, exist_ok=True)
            log_path = os.path.join(self.log_dir, self.log_file)
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s %(levelname)s %(message)s',
                handlers=[
                    logging.FileHandler(log_path),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger("EEGPreprocessingTools")
        else:
            # Use the passed logger
            self.logger = logger

        # Log the initialization
        self.logger.info("EEG Preprocessing module initialized.")

    def apply_ica(self, raw):
        """
        Computes an ICA and automatically excludes EOG and ECG artifacts.

        Parameters:
            raw (mne.io.Raw): The EEG data.

        Returns:
            mne.io.Raw: The EEG data after artifact removal.
        Note:
            The ICA object is not returned. If you need the ICA object, modify the function to return it explicitly.
        """
        self.logger.info("Starting ICA computation.")

        # Fit the ICA
        ica = mne.preprocessing.ICA(n_components=40, random_state=97, max_iter="auto")
        ica.fit(raw)
        # ica.plot_components()
        # ica.plot_sources(raw)

        # Detect EOG artifacts
        try:
            eog_indices, _ = ica.find_bads_eog(raw)  # Default detection
            self.logger.info("EOG artifacts detected.")

        except RuntimeError as e:
            # Handle the case where no EOG channels exist
            self.logger.warning(
                "No EOG channels found. Using frontal channels as substitutes."
            )
            eog_indices, _ = ica.find_bads_eog(
                raw, ch_name=["Fp1.", "Fp2."]
            )  # Substitutes

        # Combine indices and mark them for exclusion
        ica.exclude = eog_indices

        # Apply ICA to remove artifacts
        ica.apply(raw)
        self.logger.info("ICA applied, and artifacts removed.")

        # Return the cleaned raw data and the ICA object
        return raw

    def band_filter(self, raw, lower, middle_1, middle_2, upper, combine_bands=False):
        """
        Applies a custom band-pass filter to EEG data and optionally combines two frequency bands.

        Parameters:
            raw (mne.io.Raw): The EEG data to be filtered.
            lower (float): The lower frequency limit in Hz for the first filter.
            middle_1 (float): The upper frequency limit for the first filter.
            middle_2 (float): The lower frequency limit for the second filter.
            upper (float): The upper frequency limit in Hz for the second filter.
            combine_bands (bool): If True, applies sequential filters for two bands (e.g., Theta and Alpha).

        Returns:
            mne.io.Raw: The filtered EEG data. If combine_bands=True, the output is the result of sequentially applying both band-pass filters.
        """

        # Inform about the custom filter range
        self.logger.info(
            f"Applying custom band-pass filter with {lower} Hz - {middle_1} Hz - {middle_2} Hz - {upper} Hz."
        )

        # Apply the first band-pass filter
        raw.filter(lower, middle_1, fir_design="firwin", skip_by_annotation="edge")
        # Apply the second band-pass filter
        raw.filter(middle_2, upper, fir_design="firwin", skip_by_annotation="edge")

        self.logger.info("Custom band-pass filter applied.")

        if combine_bands:
            # Example: Combine Theta (4-8 Hz) with Alpha (8-13 Hz)
            self.logger.info("Combining bands into one output.")

            # Apply Theta (4-8 Hz)
            raw.filter(4, 8, fir_design="firwin", skip_by_annotation="edge")

            # Apply Alpha (8-13 Hz)
            raw.filter(8, 13, fir_design="firwin", skip_by_annotation="edge")

            # Optionally you can average or combine the two band-pass filtered results if needed
            # For simplicity, let's just apply the filters sequentially and return the result.

            self.logger.info("Bands combined into single output.")

        return raw

    def set_reference_channel(self, raw, reference):
        """
        Sets the EEG reference channel(s) for the raw data.

        Parameters:
            raw (mne.io.Raw): The EEG data to process.
            reference (Union[str, List[str]]): The reference channel(s). Pass a string for a single channel or a list for multiple channels.

        Returns:
            mne.io.Raw: The re-referenced raw data.
        """
        self.logger.info(f"Setting reference channel(s) {reference}.")

        # Check available channel names
        channel_names = raw.info["ch_names"]

        missing_references = [ref for ref in reference if ref not in channel_names]
        if missing_references:
            self.logger.error(
                f"Reference channel(s) {missing_references} not found in the dataset!"
            )
            raise ValueError(
                f"Reference channel(s) {missing_references} not found in the dataset!"
            )

        # Set the reference channel(s)
        raw.set_eeg_reference(ref_channels=reference)
        self.logger.info("Reference channel(s) set.")

        return raw

    def set_common_average_as_reference(self, raw):
        """
        Sets the common average reference for the EEG data.

        Parameters:
            raw (mne.io.Raw): The EEG data.

        Returns:
            mne.io.Raw: The EEG data with the common average reference applied.
        """

        self.logger.info("Applying common average reference.")
        # Apply the common average reference
        raw.set_eeg_reference(ref_channels="average")
        self.logger.info("Common average reference applied.")

        return raw
    
    def reshape_eeg(self, eeg_flat: list, sample_size: int) -> tuple:
        """
        Reshape flat EEG data array to (channels, samples) format.
        
        Parameters:
            eeg_flat (list): Flattened EEG data array
            sample_size (int): Number of samples per channel
            
        Returns:
            tuple: (eeg_array, sample_size) where eeg_array is shaped (channels, samples)
        """
        eeg_array = np.array(eeg_flat, dtype=np.float64)
        num_channels = len(eeg_array) // sample_size
        
        if len(eeg_array) % sample_size != 0:
            self.logger.warning(f"EEG data length {len(eeg_array)} not evenly divisible by sample_size {sample_size}")
            # Trim to make it evenly divisible
            eeg_array = eeg_array[:num_channels * sample_size]
        
        eeg_array = eeg_array.reshape(num_channels, sample_size)
        self.logger.debug(f"Reshaped EEG data to {eeg_array.shape}")
        
        return eeg_array, sample_size
    
    def apply_bandpass_filter_numpy(self, eeg_array: np.ndarray, l_freq: float, h_freq: float, sfreq: float = 256.0) -> np.ndarray:
        """
        Apply bandpass filter to numpy array EEG data (lightweight, no MNE required).
        
        Parameters:
            eeg_array (np.ndarray): EEG data shaped (channels, samples)
            l_freq (float): Low frequency cutoff in Hz
            h_freq (float): High frequency cutoff in Hz
            sfreq (float): Sampling frequency in Hz (default: 256)
            
        Returns:
            np.ndarray: Filtered EEG data with same shape
        """
        from scipy.signal import butter, sosfiltfilt
        
        n_samples = eeg_array.shape[1]
        
        # Check if we have enough samples for proper filtering
        # Rule of thumb: need at least 3 cycles of the lowest frequency
        min_samples = int(3 * (sfreq / l_freq))
        if n_samples < min_samples:
            self.logger.warning(
                f"Segment has {n_samples} samples, recommended minimum is {min_samples} "
                f"for {l_freq} Hz filter. Results may have edge artifacts."
            )
        
        # Design butterworth bandpass filter using second-order sections (more stable)
        nyq = sfreq / 2.0
        low = l_freq / nyq
        high = h_freq / nyq
        
        if low <= 0 or high >= 1:
            self.logger.warning(f"Invalid filter frequencies: {l_freq}-{h_freq} Hz for sfreq={sfreq}")
            return eeg_array
        
        # Use 4th order filter for proper frequency response
        # With buffering, we have enough samples to handle this
        filter_order = 4
        sos = butter(filter_order, [low, high], btype='band', output='sos')
        
        # Apply zero-phase filter to each channel using second-order sections
        filtered = np.zeros_like(eeg_array)
        for ch_idx in range(eeg_array.shape[0]):
            filtered[ch_idx, :] = sosfiltfilt(sos, eeg_array[ch_idx, :])
        
        self.logger.debug(f"Applied {filter_order}th-order bandpass filter {l_freq}-{h_freq} Hz on {n_samples} samples")
        return filtered
    
    def apply_common_average_reference_numpy(self, eeg_array: np.ndarray) -> np.ndarray:
        """
        Apply common average reference to numpy EEG data.
        
        Parameters:
            eeg_array (np.ndarray): EEG data shaped (channels, samples)
            
        Returns:
            np.ndarray: Referenced EEG data with same shape
        """
        # Compute mean across all channels for each time point
        avg_ref = np.mean(eeg_array, axis=0, keepdims=True)
        
        # Subtract common average from each channel
        referenced = eeg_array - avg_ref
        
        self.logger.debug("Applied common average reference")
        return referenced