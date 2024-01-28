# Home Assistant Integration of Moj Elektro electricity meter

This is an updated version of the custom component for integrating electric utility meter data into Home Assistant. It no longer requires a local certificate to access Mojelektro but utilizes a new API service provided by Informatika.si.

### Warning for existing users:
This update will not erase any existing sensors but will not update the energy produced (_output) entities.


### Setup API:

1. Log in to Mojelektro.si using any available login options.
2. Under Moj Profil, find the option to create a token (Kreiraj žeton). Use unlimited expiration and click "Create Token."
4. Copy the newly generated token. You'll need it in the next step.



### Installation

1. Copy this folder to `<config_dir>/custom_components/mojelektro/`.
2. Add the following entry in your `configuration.yaml`:
   
    ```yaml
    mojelektro:
      token: <your-token-from-mojelektro>
      meter_id: <your-meter-id>
    ```
