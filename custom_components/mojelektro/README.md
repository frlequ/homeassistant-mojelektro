# Home Assistant Integration of Moj Elektro electricity meter

This is custom component for integrating electric utility meter data into Home Assistant.  
As mojelektro.si requires 2 factor authentication, this solution uses key-cert login.  
Unfortunately self signed certs don't works as it needs to be signed by one of the following CA

```
Acceptable client certificate CA names
C = SI, O = ACNLB
C = SI, O = POSTA, OU = POSTArCA
C = SI, O = Halcom, CN = Halcom CA FO
C = SI, O = Halcom, CN = Halcom CA PO 2
C = SI, O = Halcom d.d., CN = Halcom CA PO 3
C = SI, O = OSI d.o.o., CN = OSI.SI Root CA 1
C = si, O = state-institutions, OU = sigen-ca
C = si, O = state-institutions, OU = sigov-ca
C = SI, O = OSI d.o.o., CN = OSI.SI Private CA 1
C = SI, O = NLB d.d., organizationIdentifier = VATSI-91132550, CN = ACNLB SubCA
C = SI, O = NLB d.d., organizationIdentifier = VATSI-91132550, CN = ACNLB RootCA
C = SI, O = Republika Slovenija, organizationIdentifier = VATSI-17659957, CN = SIGOV-CA
C = SI, O = Republika Slovenija, organizationIdentifier = VATSI-17659957, CN = SIGEN-CA G2
C = SI, O = Republika Slovenija, organizationIdentifier = VATSI-17659957, CN = SI-TRUST Root
C = SI, O = POSTA SLOVENIJE d.o.o., organizationIdentifier = VATSI-25028022, CN = POSTArCA G2
C = SI, O = POSTA SLOVENIJE d.o.o., organizationIdentifier = VATSI-25028022, CN = POSTArCA Root
C = SI, O = Halcom d.d., organizationIdentifier = VATSI-43353126, CN = Halcom CA FO e-signature 1
C = SI, O = Halcom d.d., organizationIdentifier = VATSI-43353126, CN = Halcom CA PO e-signature 1
C = SI, O = Halcom d.d., organizationIdentifier = VATSI-43353126, CN = Halcom Root Certificate Authority
```

Also as the data is always reported for the previous day, and I couldn't find a way to tell HA to log sensor data to the past, data will always be one day off.

(The code is based on https://github.com/home-assistant/example-custom-config/tree/master/custom_components/example_load_platform)

### Installation

1. Copy this folder to `<config_dir>/custom_components/mojelektro/`.

2. Copy your certificate key and cert to the folder location from 1.  
You have to name them `crt.pem` and `key.pem`. If you only have the .p12 file you can use the following command.
    ```shell script
    openssl pkcs12 -in path.p12 -out crt.pem -clcerts -nokeys
    openssl pkcs12 -in path.p12 -out key.pem -nocerts -nodes
    ```

3. Add the following entry in your `configuration.yaml`:
    ```yaml
    mojelektro:
      username: <your-email>
      password: <your-password>
      meter_id: <your-meter-id>
    ```
