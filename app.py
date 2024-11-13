from flask import Flask, request, jsonify
import requests, os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Shopify and DPD API configuration from environment
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_API_PASSWORD = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_API_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-10"
DPD_API_BASE_URL = os.getenv("DPD_API_BASE_URL")
DPD_CLIENT_ID = os.getenv("DPD_CLIENT_ID")
DPD_CLIENT_SECRET = os.getenv("DPD_CLIENT_SECRET")
DPD_ACCOUNT_NO = os.getenv("DPD_ACCOUNT_NO")


service_level = {
    "Economy": "ECON",
    "Express": "SDX",
    }

def fetch_order_details(order_id):
    """
    Retrieve Shopify order details by ID.

    Parameters:
        order_id (str): Shopify order ID.

    Returns:
        dict: Order data if successful, None otherwise.
    """
    url = f"{SHOPIFY_API_URL}/orders/{order_id}.json"
    headers = {"X-Shopify-Access-Token": SHOPIFY_API_PASSWORD, "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json().get("order") if response.status_code == 200 else None

def inject_waybill(waybill_data, order_id):
    """
    Inject waybill data into DPD system.

    Parameters:
        waybill_data (dict): Data for waybill injection.

    Returns:
        dict: Injection response from DPD API.
    """
    url = f"{DPD_API_BASE_URL}/api/Injection/InjectWaybill/{waybill_data['WaybillNo']}/true/false"
    response = requests.post(url, json=waybill_data)

    response_data = response.json()

    #Checks for successful injection or existing waybill
    if response_data.get("responseCode") in [200,202]:
        # Extract label URLs
        label_urls = response_data.get("responseData")
        # Add the label URLs to the Shopify order note
        download_PDF(label_urls)
        return {
            "status": "success",
            "message": response_data.get("responseMessage"),
            "label_urls": label_urls
        }
    else:
        return{
            "status": "error",
            "message": response_data.get("responseMessage")
        }
    #response.json() if response.status_code == 200 else {"error": "Waybill injection failed"}

def process_order(order_data):
    """
    Processes an order by preparing waybill data and injecting it into DPD.

    Parameters:
        order_data (dict): Order data from Shopify.

    Returns:
        dict: Result of waybill injection.
    """

    waybill_data = {
    "WaybillInjectID": int(custom_order_no(order_data.get("order_number"))[len(custom_order_no(order_data.get("order_number")))-4:]),
    "WaybillNo": custom_order_no(order_data.get("order_number")),
    "CollectionNumber": custom_order_no(order_data.get("order_number")),
    "Account": DPD_ACCOUNT_NO,
    "AccountSiteID": 0,
    "Service": service_level[order_data.get("shipping_lines")[0]["code"]],
    "ServiceLevel": service_level[order_data.get("shipping_lines")[0]["code"]],
    "LoadType": None,
    "WaybillType": 2,
    "Packets": max(len(order_data.get("line_items", [])), 1),
    "ParcelCount": len(order_data.get("line_items")),
    "Department": "",
    "CustomerDeptartment": "",
    "Insurance": 0.0,
    "Transporter": "DPD",
    "Sender": {
        "Consignor": "Little Brand Box",
        "StreetNo": "100",
        "StreetNumber": "",
        "StreetName": "100 Voortrekker Rd",
        "Complex": "",
        "Building": "The Spice Yard",
        "UnitNo": "",
        "BuildingNumber": "",
        "Suburb": "Salt River",
        "Town": "CAPE TOWN",
        "City": "CAPE TOWN",
        "PostCode": "7925",
        "StoreCode": "",
        "Latitude": "-33.925786",
        "Longitude": "18.470066"
    },
    "Consignee": {
        "Consignee": order_data.get("shipping_address", {}).get("name", "Unknown Receiver"),
        "StreetNo": "",
        "StreetNumber": order_data.get("shipping_address", {}).get("address1", "").split()[0] if order_data.get("shipping_address", {}).get("address1") else "",
        "StreetName": order_data.get("shipping_address", {}).get("address1", ""),
        "Complex": "",
        "Building": order_data.get("shipping_address", {}).get("address1", ""),
        "UnitNo": "",
        "BuildingNumber": "",
        "Suburb": order_data.get("shipping_address", {}).get("city", ""),
        "Town": order_data.get("shipping_address", {}).get("province", ""),
        "City": order_data.get("shipping_address", {}).get("province", ""),
        "PostCode": order_data.get("shipping_address", {}).get("zip", ""),
        "StoreCode": "",
        "Latitude": order_data.get("shipping_address", {}).get("latitude", ""),
        "Longitude": order_data.get("shipping_address", {}).get("longitude", "")
    },

    "CustomerRef": "",
    "PrintLabel": False,
    "WaybillTypeName": None,
    "Parcels": [
        {
            "Barcode": custom_order_no(order_data.get("order_number")),
            "Length": 42.0,
            "Width": 38.0,
            "Height": 10.0,
            "Weight": 1.0,
            "Decription": "MY BIG BOX",
            "ParcelContent": ""
        }
    ],
    "References": [],
    "Notes": [],
    "SpecialInstructions": [],
    "WaybillInstructions": [],
    "Contacts": [],
    "SenderContacts": {
        "FirstName": "Little Brand Box",
        "Surname": "Company",
        "Telephone": "",
        "CellPhone": "0214236868",
        "Email": "malcolm@littlebrandbox.com",
        "IDNumber": ""
    },
    "ReceiverContacts": {
        "FirstName": "ReceiverName",
        "Surname": "ReceiverSurname",
        "Telephone": "",
        "CellPhone": "0832222222",
        "Email": "receiver@somewhere.com",
        "IDNumber": ""
    },
    "Content": [],
    "UniqueReference": None,
    "PromiseDate": None,
    "DateCreated": None,
    "WaybillInstruction": "",
    "InjectionReference": "945BFB53-FFEA-4FAF-9BF3-8FA48127B5ED",
    "ReadyforCollectDate": "2023-07-13T08:00:00",
    "CollectAfterTime": "17:00:00",
    "CollectBeforeTime": "19:00:00",
    "DeliveryOTP": None,
    "AltDeliveryCode": None,
    "PickUpID": 0,
    "PickUpNo": "Pickup_Number_which_waybills_will_link_to",
    "CreatingUser": "",
    "CreatingUserID": 1,
    "DeliveryBookDate": None,
    "IsInternational": False
    }

    result = inject_waybill(waybill_data)
    return result if result.get("ID") != 0 else inject_waybill(waybill_data)

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Handles Shopify webhook, processes order, and injects waybill.

    Returns:
        JSON: Status of operation and delivery data.
    """
    data = request.json

    if not data or "id" not in data:
        return jsonify({"status": "error", "message": "Invalid request data"}), 400

    order_data = fetch_order_details(data["id"])
    if not order_data:
        return jsonify({"status": "error", "message": "Order not found on Shopify"}), 404

    delivery_data = process_order(order_data)
    return jsonify({"status": "success", "delivery_data": delivery_data}), 200





# Utility Methods
def custom_order_no(order_no):
    """
    Generate custom order number by appending order number to base prefix.

    Parameters:
        order_no (str): Original order number.

    Returns:
        str: Custom formatted order number.
    """
    base_prefix = "HAR888008"
    return f"{base_prefix}{str(order_no).zfill(4)}"

# Download PDFs from DPD Waybill
def download_PDF(label_urls):
    """
    Updates the Shopify order note with DPD label URLs.
    """
    pdf_files = []
    for url in label_urls:
        response = requests.get(url)
        if response.status_code == 200:
            pdf_files.append(response.content)  # Store binary content of PDF
            return pdf_files
        else:
            return f"Failed to download PDF from {url}"

# GraphQL fileCreate mutation template
def create_file_mutation(filename, file_data):
    return {
        "query": """
        mutation fileCreate($files: [FileCreateInput!]!) {
            fileCreate(files: $files) {
                files {
                    id
                    alt
                    createdAt
                    fileStatus
                    originalFileSize
                    preview {
                        image {
                            id
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """,
        "variables": {
            "files": [
                {
                    "alt": filename,
                    "contentType": "APPLICATION_PDF",
                    "originalSource": file_data
                }
            ]
        }
    }

# Upload to shopify
def upload_to_shopify(pdf_files, headers):
    for i, pdf_content in enumerate(pdf_files):
        pdf_base64 = base64.b64encode(pdf_content).decode("utf-8")  # Encode PDF to base64 for Shopify
        filename = f"label_{i+1}.pdf"
        mutation = create_file_mutation(filename, pdf_base64)
    
        response = requests.post(shopify_url, headers=headers, json=mutation)
        if response.status_code == 200:
            print(f"Successfully uploaded {filename}")
        else:
            print(f"Failed to upload {filename}: {response.json()}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)