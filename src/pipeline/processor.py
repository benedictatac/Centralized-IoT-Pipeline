### Receives raw message and validates it and transforms into the BaseModel structure 
# If valid, returns a valid Device object. Specific to Pydantic models     
####



from src.models.baseModel import BaseModel, Device, DeviceType, Metric, Unit, Reading
from pydantic import ValidationError
import logging 
import json




def process_message(msg) -> Device:

        #case of msg being NONE | empty 
        if msg is None or getattr(msg, 'payload', None) is None:
            return None
        
        try:
            if msg.topic:
                print(f"Received message on topic: {msg.topic}", flush = True)
            data = parse_json_payload(msg=msg)
            if data is None:
                return None
            print(f"Parsed Data is {data}")
            data_validated = Device.model_validate(data)
            return data_validated
        except ValidationError as e: 
            print(f"Validation failed. Schema does not correspond")
            print(e.errors())
        except Exception as e: 
            print(f"Error processing message on topic '{getattr(msg, 'topic', 'unknown')}': {e}", flush=True)   


            #parsing to return dict structure 
def parse_json_payload(msg) -> dict | None:
         try: 
            parsed_json = msg.payload.decode("utf-8")
            return json.loads(parsed_json)
         except (UnicodeError, AttributeError) as e: 
            logging.error(f"Failed to decode message on {msg.topic}: payload is not valid UTF-8 text.")
            return None
         except json.JSONDecodeError as err:
            logging.error(f"JSON parsing error on topic '{msg.topic}': {err}")
            logging.debug(f"Raw raw text was: {msg.payload}")
            return None


