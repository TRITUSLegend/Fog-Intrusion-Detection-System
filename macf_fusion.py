class MACFFusion:
    def __init__(self, tau_base=25):
        self.tau_base = tau_base
        self.IPS = 0.0

    def compute_erf(self, ldr_val):
        """
        Compute Environmental Risk Factor.
        Higher LDR value (brighter) -> lower ERF.
        """
        erf = 1.0 - (ldr_val / 1023.0)
        return max(0.0, min(1.0, erf))

    def compute_tau_adaptive(self, erf):
        """
        Compute dynamic threshold based on base threshold and ERF.
        Higher ERF -> lower threshold (more sensitive in dark).
        """
        tau_adaptive = self.tau_base * (1.0 - 0.4 * erf)
        return int(max(0, tau_adaptive))

    def compute_fusion(self, pir_val, ldr_val, c_vid):
        """
        Fuses multimodal sensor values into an Intrusion Probability Score (IPS).
        Returns ERF, tau_adaptive, and IPS.
        """
        # Step 2: ERF
        erf = self.compute_erf(ldr_val)

        # Step 3: Adaptive Threshold
        tau_adaptive = self.compute_tau_adaptive(erf)

        # Step 4: PIR Confidence
        c_pir = 1.0 if pir_val == 1 else 0.0

        # Step 6: Intrusion Probability Fusion
        ips_raw = (0.50 * c_pir) + (0.20 * erf) + (0.30 * c_vid)

        # Step 7: Temporal Smoothing
        if c_pir == 0.0 and c_vid < 0.1:
            self.IPS = self.IPS * (1.0 - 0.40)
        else:
            self.IPS = self.IPS * (1.0 - 0.40) + ips_raw * 0.40

        # Clamp IPS
        self.IPS = max(0.0, min(1.0, self.IPS))

        return erf, tau_adaptive, self.IPS
