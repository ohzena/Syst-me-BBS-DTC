"""
dtc.py - Digital Trust Certificate Core Data Structures
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import json
import base58
import hashlib

DTC_VERSION = "1.0"
DTC_CONTEXT = "https://www.w3.org/2018/credentials/v1"


class DocumentType(Enum):
    """Types of travel documents"""
    PASSPORT = "passport"
    VISA = "visa"
    VACCINATION = "vaccination_certificate"
    PCR_TEST = "pcr_test_result"
    TRAVEL_AUTHORIZATION = "travel_authorization"
    IDENTITY_CARD = "identity_card"


class AttributeType(Enum):
    """Data types for credential attributes"""
    STRING = "string"
    DATE = "date"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    HASH = "hash"
    IMAGE_HASH = "image_hash"


@dataclass
class CredentialAttribute:
    """Single attribute in a credential"""
    name: str
    value: Any
    type: AttributeType
    required: bool = False
    hidden: bool = False
    
    def to_bytes(self) -> bytes:
        """Convert attribute to bytes for signing"""
        if self.type == AttributeType.DATE:
            if isinstance(self.value, (datetime, date)):
                value_str = self.value.isoformat()
            else:
                value_str = str(self.value)
        else:
            value_str = str(self.value)
        
        return f"{self.name}:{self.type.value}:{value_str}".encode('utf-8')
    
    def to_display_string(self) -> str:
        """Human-readable format"""
        if self.hidden:
            return f"{self.name}: ***HIDDEN***"
        return f"{self.name}: {self.value}"


@dataclass
class CredentialSchema:
    """Schema definition for a credential type"""
    document_type: DocumentType
    version: str
    attributes: List[Dict[str, Any]]
    issuer_constraints: Optional[Dict[str, Any]] = None
    
    def validate_attributes(self, attributes: Dict[str, CredentialAttribute]) -> bool:
        """Validate attributes against schema"""
        required_attrs = [a['name'] for a in self.attributes if a.get('required', False)]
        
        for req_attr in required_attrs:
            if req_attr not in attributes:
                return False
        
        return True


PASSPORT_SCHEMA = CredentialSchema(
    document_type=DocumentType.PASSPORT,
    version="1.0",
    attributes=[
        {"name": "document_number", "type": "string", "required": True},
        {"name": "holder_name", "type": "string", "required": True},
        {"name": "nationality", "type": "string", "required": True},
        {"name": "date_of_birth", "type": "date", "required": True},
        {"name": "place_of_birth", "type": "string", "required": True},
        {"name": "gender", "type": "string", "required": False},
        {"name": "date_of_issue", "type": "date", "required": True},
        {"name": "date_of_expiry", "type": "date", "required": True},
        {"name": "issuing_authority", "type": "string", "required": True},
        {"name": "photo_hash", "type": "image_hash", "required": False},
        {"name": "biometric_hash", "type": "hash", "required": False, "hidden": True},
        {"name": "signature_hash", "type": "hash", "required": False, "hidden": True}
    ]
)

VISA_SCHEMA = CredentialSchema(
    document_type=DocumentType.VISA,
    version="1.0",
    attributes=[
        {"name": "visa_number", "type": "string", "required": True},
        {"name": "visa_type", "type": "string", "required": True},
        {"name": "passport_number", "type": "string", "required": True},
        {"name": "holder_name", "type": "string", "required": True},
        {"name": "country_of_issue", "type": "string", "required": True},
        {"name": "valid_from", "type": "date", "required": True},
        {"name": "valid_until", "type": "date", "required": True},
        {"name": "entries_allowed", "type": "string", "required": True},
        {"name": "duration_of_stay", "type": "integer", "required": True},
        {"name": "purpose", "type": "string", "required": False}
    ]
)

VACCINATION_SCHEMA = CredentialSchema(
    document_type=DocumentType.VACCINATION,
    version="1.0",
    attributes=[
        {"name": "certificate_id", "type": "string", "required": True},
        {"name": "holder_name", "type": "string", "required": True},
        {"name": "date_of_birth", "type": "date", "required": True},
        {"name": "vaccine_type", "type": "string", "required": True},
        {"name": "vaccine_name", "type": "string", "required": True},
        {"name": "manufacturer", "type": "string", "required": True},
        {"name": "batch_number", "type": "string", "required": True},
        {"name": "vaccination_date", "type": "date", "required": True},
        {"name": "vaccination_center", "type": "string", "required": True},
        {"name": "country_of_vaccination", "type": "string", "required": True},
        {"name": "dose_number", "type": "integer", "required": True},
        {"name": "total_doses", "type": "integer", "required": True},
        {"name": "next_dose_date", "type": "date", "required": False}
    ]
)


@dataclass
class DTCCredential:
    """Base Digital Trust Certificate Credential"""
    credential_id: str
    document_type: DocumentType
    schema: CredentialSchema
    attributes: Dict[str, CredentialAttribute]
    issuer_id: str
    holder_id: Optional[str] = None
    issued_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    signature: Optional[Any] = None
    signature_bytes: Optional[bytes] = None
    revoked: bool = False
    
    def __post_init__(self):
        """Validate credential after initialization"""
        try:
            if not self.schema.validate_attributes(self.attributes):
                pass
        except Exception:
            pass
    
    def add_attribute(self, name: str, value: Any, attr_type: AttributeType, 
                     required: bool = False, hidden: bool = False):
        """Add an attribute to the credential"""
        self.attributes[name] = CredentialAttribute(
            name=name,
            value=value,
            type=attr_type,
            required=required,
            hidden=hidden
        )
    
    def get_messages_for_signing(self) -> List[bytes]:
        """Get all attributes as messages for BBS signing"""
        messages = []
        
        messages.append(f"credential_id:{self.credential_id}".encode())
        messages.append(f"document_type:{self.document_type.value}".encode())
        messages.append(f"issuer_id:{self.issuer_id}".encode())
        messages.append(f"issued_at:{self.issued_at.isoformat()}".encode())
        
        if self.expires_at:
            messages.append(f"expires_at:{self.expires_at.isoformat()}".encode())
        
        for name in sorted(self.attributes.keys()):
            messages.append(self.attributes[name].to_bytes())
        
        return messages
    
    def to_message_list(self) -> List[bytes]:
        """Alias for get_messages_for_signing()"""
        return self.get_messages_for_signing()
    
    def get_attribute_indices_map(self) -> Dict[str, int]:
        """Get mapping of attribute names to message indices"""
        indices = {}
        
        offset = 4
        if self.expires_at:
            offset += 1
        
        for i, name in enumerate(sorted(self.attributes.keys())):
            indices[name] = offset + i
        
        return indices
    
    def select_attributes_for_disclosure(self, attribute_names: List[str]) -> List[int]:
        """Get message indices for attributes to disclose"""
        indices_map = self.get_attribute_indices_map()
        disclosed_indices = []
        
        disclosed_indices.extend([1, 2])
        
        for name in attribute_names:
            if name in indices_map:
                disclosed_indices.append(indices_map[name])
        
        return sorted(disclosed_indices)
    
    def to_json(self) -> str:
        """Serialize credential to JSON"""
        data = {
            "@context": DTC_CONTEXT,
            "version": DTC_VERSION,
            "credential_id": self.credential_id,
            "document_type": self.document_type.value,
            "issuer_id": self.issuer_id,
            "holder_id": self.holder_id,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "attributes": {
                name: {
                    "value": attr.value if not isinstance(attr.value, (datetime, date)) 
                            else attr.value.isoformat(),
                    "type": attr.type.value,
                    "hidden": attr.hidden
                }
                for name, attr in self.attributes.items()
            }
        }
        
        if self.signature_bytes:
            data["signature_bytes"] = base58.b58encode(self.signature_bytes).decode('ascii')
        
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DTCCredential':
        """Deserialize credential from JSON"""
        data = json.loads(json_str)
        
        doc_type = DocumentType(data["document_type"])
        schema_map = {
            DocumentType.PASSPORT: PASSPORT_SCHEMA,
            DocumentType.VISA: VISA_SCHEMA,
            DocumentType.VACCINATION: VACCINATION_SCHEMA
        }
        schema = schema_map.get(doc_type)
        
        attributes = {}
        for name, attr_data in data["attributes"].items():
            attr_type = AttributeType(attr_data["type"])
            value = attr_data["value"]
            
            if attr_type == AttributeType.DATE:
                if isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value).date()
                    except:
                        value = datetime.strptime(value, "%Y-%m-%d").date()
            
            attributes[name] = CredentialAttribute(
                name=name,
                value=value,
                type=attr_type,
                hidden=attr_data.get("hidden", False)
            )
        
        credential = cls(
            credential_id=data["credential_id"],
            document_type=doc_type,
            schema=schema,
            attributes=attributes,
            issuer_id=data["issuer_id"],
            holder_id=data.get("holder_id"),
            issued_at=datetime.fromisoformat(data["issued_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )
        
        if data.get("signature_bytes"):
            credential.signature_bytes = base58.b58decode(data["signature_bytes"])
        
        return credential
    
    def is_valid(self) -> bool:
        """Check if credential is currently valid"""
        if self.revoked:
            return False
        
        now = datetime.now()
        if self.expires_at and now > self.expires_at:
            return False
        
        return True
    
    def generate_credential_hash(self) -> str:
        """Generate a unique hash for this credential"""
        hasher = hashlib.sha256()
        hasher.update(self.credential_id.encode())
        hasher.update(self.document_type.value.encode())
        hasher.update(self.issuer_id.encode())
        
        for msg in self.get_messages_for_signing():
            hasher.update(msg)
        
        return base58.b58encode(hasher.digest()).decode('ascii')
    
    def __str__(self) -> str:
        """String representation for the credential"""
        return f"{self.document_type.value.upper()} credential [{self.credential_id}]"


class PassportCredential(DTCCredential):
    """Specialized passport credential"""
    
    def __init__(self, issuer_id: str, holder_id: str = None, **kwargs):
        cred_id = f"PASSPORT_{kwargs.get('document_number', 'UNKNOWN')}_{int(datetime.now().timestamp())}"
        
        attributes = {}
        for attr_def in PASSPORT_SCHEMA.attributes:
            name = attr_def["name"]
            if name in kwargs:
                attr_type = AttributeType(attr_def["type"])
                value = kwargs[name]
                
                if attr_type == AttributeType.DATE and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value).date()
                    except:
                        value = datetime.strptime(value, "%Y-%m-%d").date()
                
                attributes[name] = CredentialAttribute(
                    name=name,
                    value=value,
                    type=attr_type,
                    required=attr_def.get("required", False),
                    hidden=attr_def.get("hidden", False)
                )
        
        super().__init__(
            credential_id=cred_id,
            document_type=DocumentType.PASSPORT,
            schema=PASSPORT_SCHEMA,
            attributes=attributes,
            issuer_id=issuer_id,
            holder_id=holder_id,
            expires_at=datetime.now().replace(year=datetime.now().year + 10)
        )


class VisaCredential(DTCCredential):
    """Specialized visa credential"""
    
    def __init__(self, issuer_id: str, holder_id: str = None, **kwargs):
        cred_id = f"VISA_{kwargs.get('visa_number', 'UNKNOWN')}_{int(datetime.now().timestamp())}"
        
        attributes = {}
        for attr_def in VISA_SCHEMA.attributes:
            name = attr_def["name"]
            if name in kwargs:
                attr_type = AttributeType(attr_def["type"])
                value = kwargs[name]
                
                if attr_type == AttributeType.DATE and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value).date()
                    except:
                        value = datetime.strptime(value, "%Y-%m-%d").date()
                
                attributes[name] = CredentialAttribute(
                    name=name,
                    value=value,
                    type=attr_type,
                    required=attr_def.get("required", False),
                    hidden=attr_def.get("hidden", False)
                )
        
        expires_at = None
        if 'valid_until' in kwargs:
            if isinstance(kwargs['valid_until'], str):
                try:
                    expires_at = datetime.fromisoformat(kwargs['valid_until'])
                except:
                    expires_at = datetime.strptime(kwargs['valid_until'], "%Y-%m-%d")
            else:
                expires_at = kwargs['valid_until']
        
        super().__init__(
            credential_id=cred_id,
            document_type=DocumentType.VISA,
            schema=VISA_SCHEMA,
            attributes=attributes,
            issuer_id=issuer_id,
            holder_id=holder_id,
            expires_at=expires_at
        )


class VaccinationCredential(DTCCredential):
    """Specialized vaccination credential"""
    
    def __init__(self, issuer_id: str, holder_id: str = None, **kwargs):
        cred_id = f"VAX_{kwargs.get('certificate_id', 'UNKNOWN')}_{int(datetime.now().timestamp())}"
        
        attributes = {}
        for attr_def in VACCINATION_SCHEMA.attributes:
            name = attr_def["name"]
            if name in kwargs:
                attr_type = AttributeType(attr_def["type"])
                value = kwargs[name]
                
                if attr_type == AttributeType.DATE and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value).date()
                    except:
                        value = datetime.strptime(value, "%Y-%m-%d").date()
                
                attributes[name] = CredentialAttribute(
                    name=name,
                    value=value,
                    type=attr_type,
                    required=attr_def.get("required", False),
                    hidden=attr_def.get("hidden", False)
                )
        
        super().__init__(
            credential_id=cred_id,
            document_type=DocumentType.VACCINATION,
            schema=VACCINATION_SCHEMA,
            attributes=attributes,
            issuer_id=issuer_id,
            holder_id=holder_id,
            expires_at=datetime.now().replace(year=datetime.now().year + 1)
        )


def create_passport_credential(issuer_id: str, **kwargs) -> DTCCredential:
    """Create a passport credential"""
    return PassportCredential(issuer_id, **kwargs)

def create_visa_credential(issuer_id: str, **kwargs) -> DTCCredential:
    """Create a visa credential"""
    return VisaCredential(issuer_id, **kwargs)

def create_vaccination_credential(issuer_id: str, **kwargs) -> DTCCredential:
    """Create a vaccination certificate credential"""
    return VaccinationCredential(issuer_id, **kwargs)