"""
ZKProof.py - Zero-Knowledge Proof Generation and Verification
Following IETF BBS Signatures specification 
"""

import secrets
import hashlib
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from py_ecc.optimized_bls12_381 import (
    G1, G2, multiply, add, neg, pairing, final_exponentiate, 
    FQ12, curve_order, normalize, Z1, Z2
)

from py_ecc.bls.g2_primitives import G1_to_pubkey
from py_ecc.optimized_bls12_381.optimized_pairing import normalize1

from BBSCore.Setup import (
    BBSPrivateKey, BBSPublicKey, BBSGenerators,
    CURVE_ORDER, hash_to_scalar, calculate_domain,
    point_to_bytes_g1, point_from_bytes_g1
)
from BBSCore.bbsSign import BBSSignature

DST_H2S = b"BBS_BLS12381G1_XMD:SHA-256_SSWU_RO_H2S_DST_"

def affine_to_bytes(point) -> bytes:
    """Convert point to bytes (48 bytes for G1)"""
    if point is None:
        return b'\x00' * 48
    normalized = normalize1(point)
    return G1_to_pubkey(normalized)

@dataclass
class ProofInitResult:
    """Result from ProofInit operation - Core.tex Section 3.7.1"""
    T1: tuple
    T2: tuple
    Abar: tuple
    Bbar: tuple
    D: tuple
    domain: int

@dataclass
class BBSProof:
    """BBS Proof following Core.tex specification Section 3.6.3"""
    Abar: tuple
    Bbar: tuple
    D: tuple
    e_hat: int
    r1_hat: int
    r3_hat: int
    commitments: List[int]
    cp: int

    def __init__(self, Abar=None, Bbar=None, D=None,
                e_hat=None, r1_hat=None, r3_hat=None,
                commitments=None, cp=None):
        self.Abar = Abar
        self.Bbar = Bbar
        self.D = D
        self.e_hat = e_hat
        self.r1_hat = r1_hat
        self.r3_hat = r3_hat
        self.commitments = commitments or []
        self.cp = cp
    
    def to_bytes(self) -> bytes:
        """Serialize proof to bytes"""
        data = b""
        data += affine_to_bytes(self.Abar)     # 48 bytes
        data += affine_to_bytes(self.Bbar)     # 48 bytes
        data += affine_to_bytes(self.D)        # 48 bytes
        data += self.e_hat.to_bytes(32, 'big')   # 32 bytes
        data += self.r1_hat.to_bytes(32, 'big')  # 32 bytes
        data += self.r3_hat.to_bytes(32, 'big')  # 32 bytes
        data += len(self.commitments).to_bytes(4, 'big')
        for commitment in self.commitments:
            data += commitment.to_bytes(32, 'big')
        data += self.cp.to_bytes(32, 'big')      # 32 bytes
        return data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'BBSProof':
        """Deserialize proof from bytes"""
        offset = 0
        Abar = point_from_bytes_g1(data[offset:offset+48])
        offset += 48
        Bbar = point_from_bytes_g1(data[offset:offset+48])
        offset += 48
        D = point_from_bytes_g1(data[offset:offset+48])
        offset += 48
        e_hat = int.from_bytes(data[offset:offset+32], 'big')
        offset += 32
        r1_hat = int.from_bytes(data[offset:offset+32], 'big')
        offset += 32
        r3_hat = int.from_bytes(data[offset:offset+32], 'big')
        offset += 32
        num_commitments = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        commitments = []
        for _ in range(num_commitments):
            commitment = int.from_bytes(data[offset:offset+32], 'big')
            commitments.append(commitment)
            offset += 32
        cp = int.from_bytes(data[offset:offset+32], 'big')
        return cls(Abar=Abar, Bbar=Bbar, D=D, e_hat=e_hat, 
                  r1_hat=r1_hat, r3_hat=r3_hat, commitments=commitments, cp=cp)

class BBSProofScheme:
    """Zero-Knowledge Proof operations implementing Core.tex Section 3.6.3-3.6.4"""

    def __init__(self, max_messages: int = 20, api_id: bytes = b"", generators: Optional[List[tuple]] = None):
        self.max_messages = max_messages
        self.api_id = api_id
        
        if generators is not None:
            self.generators = generators
        else:
            self.generators = BBSGenerators.create_generators(self.max_messages, self.api_id)
        
        self.P1 = G1
        self.P2 = G2
    
    def calculate_random_scalars(self, count: int) -> List[int]:
        """Generate random scalars for proof"""
        return [secrets.randbelow(CURVE_ORDER - 1) + 1 for _ in range(count)]
    
    def proof_init(self,
                   PK: BBSPublicKey,
                   signature: BBSSignature,
                   random_scalars: List[int],
                   header: bytes,
                   messages: List[bytes],
                   undisclosed_indexes: List[int]) -> ProofInitResult:
        """
        ProofInit operation from Core.tex Section 3.7.1
        
        Procedure :
        1. Parse random scalars: (r1, r2, e~, r1~, r3~, m~_j1, ..., m~_jU)
        2. B = P1 + Q_1 * domain + H_1 * msg_1 + ... + H_L * msg_L  
        3. D = B * r2
        4. Abar = A * (r1 * r2)
        5. Bbar = D * r1 - Abar * e
        6. T1 = Abar * e~ + D * r1~
        7. T2 = D * r3~ + H_j1 * m~_j1 + ... + H_jU * m~_jU
        """
        # Core.tex: Parse random scalars
        r1 = random_scalars[0]
        r2 = random_scalars[1]
        e_tilde = random_scalars[2]
        r1_tilde = random_scalars[3]
        r3_tilde = random_scalars[4]
        m_tildes = random_scalars[5:]
        
        # Get generators
        L = len(messages)
        Q_1 = self.generators[0]
        H_generators = self.generators[1:L+1]
        
        # Convert messages to scalars
        msg_scalars = [hash_to_scalar(msg, self.api_id + DST_H2S) for msg in messages]
        
        # Calculate domain
        domain = calculate_domain(PK.to_bytes(), Q_1, H_generators, header, self.api_id)
        
        # Core.tex Step 2: B = P1 + Q_1 * domain + H_1 * msg_1 + ... + H_L * msg_L
        B = self.P1
        B = add(B, multiply(Q_1, domain))
        for i, msg_scalar in enumerate(msg_scalars):
            B = add(B, multiply(H_generators[i], msg_scalar))
        
        # Core.tex Step 3: D = B * r2
        D = multiply(B, r2)
        
        # Core.tex Step 4: Abar = A * (r1 * r2)
        r1_r2 = (r1 * r2) % CURVE_ORDER
        Abar = multiply(signature.A, r1_r2)
        
        # Core.tex Step 5: Bbar = D * r1 - Abar * e
        Bbar = multiply(D, r1)
        Abar_e = multiply(Abar, signature.e)
        Bbar = add(Bbar, neg(Abar_e))
        
        # Core.tex Step 6: T1 = Abar * e~ + D * r1~
        T1 = multiply(Abar, e_tilde)
        T1 = add(T1, multiply(D, r1_tilde))
        
        # Core.tex Step 7: T2 = D * r3~ + H_j1 * m~_j1 + ... + H_jU * m~_jU
        T2 = multiply(D, r3_tilde)
        undisclosed_indexes_sorted = sorted(undisclosed_indexes)
        for i, j in enumerate(undisclosed_indexes_sorted):
            if i < len(m_tildes):
                T2 = add(T2, multiply(H_generators[j], m_tildes[i]))
        
        return ProofInitResult(T1=T1, T2=T2, Abar=Abar, Bbar=Bbar, D=D, domain=domain)
    
    def proof_finalize(self,
                      init_res: ProofInitResult,
                      challenge: int,
                      e: int,
                      random_scalars: List[int],
                      undisclosed_messages: List[bytes]) -> BBSProof:
        """
        ProofFinalize operation from Core.tex Section 3.7.2
        
        Procedure :
        1. r3 = r2^-1 (mod r)
        2. e^ = e~ + e_value * challenge
        3. r1^ = r1~ - r1 * challenge
        4. r3^ = r3~ - r3 * challenge
        5. for j in (1, ..., U): m^_j = m~_j + undisclosed_j * challenge (mod r)
        """
        # Parse random scalars
        r1 = random_scalars[0]
        r2 = random_scalars[1]
        e_tilde = random_scalars[2]
        r1_tilde = random_scalars[3]
        r3_tilde = random_scalars[4]
        m_tildes = random_scalars[5:]
        
        # Convert undisclosed messages to scalars
        undisclosed_scalars = [hash_to_scalar(msg, self.api_id + DST_H2S) for msg in undisclosed_messages]
        
        # Core.tex Step 1: r3 = r2^-1 (mod r)
        r3 = pow(r2, -1, CURVE_ORDER)
        
        # Core.tex Step 2: e^ = e~ + e_value * challenge
        e_hat = (e_tilde + e * challenge) % CURVE_ORDER
        
        # Core.tex Step 3: r1^ = r1~ - r1 * challenge
        r1_hat = (r1_tilde - r1 * challenge) % CURVE_ORDER
        
        # Core.tex Step 4: r3^ = r3~ - r3 * challenge
        r3_hat = (r3_tilde - r3 * challenge) % CURVE_ORDER
        
        # Core.tex Step 5: m^_j = m~_j + undisclosed_j * challenge (mod r)
        commitments = []
        for i, msg_scalar in enumerate(undisclosed_scalars):
            if i < len(m_tildes):
                commitment = (m_tildes[i] + msg_scalar * challenge) % CURVE_ORDER
                commitments.append(commitment)
        
        return BBSProof(
            Abar=init_res.Abar, Bbar=init_res.Bbar, D=init_res.D,
            e_hat=e_hat, r1_hat=r1_hat, r3_hat=r3_hat,
            commitments=commitments, cp=challenge
        )
    
    def proof_verify_init(self,
                         PK: BBSPublicKey,
                         proof: BBSProof,
                         header: bytes,
                         disclosed_messages: List[bytes],
                         disclosed_indexes: List[int]) -> ProofInitResult:
        """
        ProofVerifyInit operation from Core.tex Section 3.7.3
        
        Procedure :
        1. Parse proof components
        2. T1 = Bbar * c + Abar * e^ + D * r1^
        3. Bv = P1 + Q_1 * domain + H_i1 * msg_i1 + ... + H_iR * msg_iR
        4. T2 = Bv * c + D * r3^ + H_j1 * m^_j1 + ... + H_jU * m^_jU
        """
        # Get total message count
        U = len(proof.commitments)
        R = len(disclosed_messages)
        L = U + R
        
        # Get generators
        Q_1 = self.generators[0]
        H_generators = self.generators[1:L+1]
        
        # Calculate domain
        domain = calculate_domain(PK.to_bytes(), Q_1, H_generators, header, self.api_id)
        
        # Core.tex Step 2: T1 = Bbar * c + Abar * e^ + D * r1^
        T1 = multiply(proof.Bbar, proof.cp)          # Bbar * challenge
        T1 = add(T1, multiply(proof.Abar, proof.e_hat))  # + Abar * e^
        T1 = add(T1, multiply(proof.D, proof.r1_hat))    # + D * r1^
        
        # Core.tex Step 3: Bv = P1 + Q_1 * domain + H_i1 * msg_i1 + ... + H_iR * msg_iR
        Bv = self.P1
        Bv = add(Bv, multiply(Q_1, domain))
        
        # Convert disclosed messages to scalars and add to Bv
        disclosed_scalars = [hash_to_scalar(msg, self.api_id + DST_H2S) for msg in disclosed_messages]
        for i, idx in enumerate(disclosed_indexes):
            if i < len(disclosed_scalars):
                Bv = add(Bv, multiply(H_generators[idx], disclosed_scalars[i]))
        
        # Core.tex Step 4: T2 = Bv * c + D * r3^ + H_j1 * m^_j1 + ... + H_jU * m^_jU
        T2 = multiply(Bv, proof.cp)                  # Bv * challenge
        T2 = add(T2, multiply(proof.D, proof.r3_hat))    # + D * r3^
        
        # Add undisclosed commitments
        disclosed_indexes_sorted = sorted(disclosed_indexes)
        undisclosed_indexes = sorted([i for i in range(L) if i not in disclosed_indexes_sorted])
        
        for i, j in enumerate(undisclosed_indexes):
            if i < len(proof.commitments):
                T2 = add(T2, multiply(H_generators[j], proof.commitments[i]))
        
        return ProofInitResult(
            T1=T1, T2=T2,
            Abar=proof.Abar, Bbar=proof.Bbar, D=proof.D,
            domain=domain
        )
    
    def proof_challenge_calculate(self,
                                 init_res: ProofInitResult,
                                 disclosed_messages: List[bytes],
                                 disclosed_indexes: List[int],
                                 ph: bytes) -> int:
        """
        ProofChallengeCalculate operation from Core.tex Section 3.7.4
        
        Challenge calculation with canonical ordering for disclosed messages
        """
        # Create pairs and sort by index for canonical order
        pairs = list(zip(disclosed_indexes, disclosed_messages))
        pairs.sort(key=lambda x: x[0])
        
        challenge_data = b""
        
        # Add proof components
        challenge_data += affine_to_bytes(init_res.Abar)
        challenge_data += affine_to_bytes(init_res.Bbar)
        challenge_data += affine_to_bytes(init_res.D)
        challenge_data += affine_to_bytes(init_res.T1)
        challenge_data += affine_to_bytes(init_res.T2)
        
        # Add domain
        challenge_data += init_res.domain.to_bytes(32, 'big')
        
        # Add disclosed messages in sorted order
        challenge_data += len(pairs).to_bytes(4, 'big')
        for idx, msg in pairs:
            challenge_data += idx.to_bytes(4, 'big')
            msg_scalar = hash_to_scalar(msg, self.api_id + DST_H2S)
            challenge_data += msg_scalar.to_bytes(32, 'big')
        
        # Add presentation header and API ID
        challenge_data += len(ph).to_bytes(8, 'big') + ph
        challenge_data += self.api_id
        
        # Hash to scalar
        dst = self.api_id + DST_H2S
        return hash_to_scalar(challenge_data, dst)
    
    def core_proof_gen(self,
                      PK: BBSPublicKey,
                      signature: BBSSignature,
                      header: bytes,
                      ph: bytes,
                      messages: List[bytes],
                      disclosed_indexes: List[int]) -> BBSProof:
        """
        CoreProofGen operation from Core.tex Section 3.6.3
        
        Procedure :
        1. Generate random scalars (5 + U scalars needed)
        2. Initialize proof using ProofInit
        3. Calculate challenge using ProofChallengeCalculate
        4. Finalize proof using ProofFinalize
        """
        L = len(messages)
        R = len(disclosed_indexes)
        
        # Validate inputs
        if R > L:
            raise ValueError("More disclosed indexes than messages")
        
        for idx in disclosed_indexes:
            if idx < 0 or idx >= L:
                raise ValueError(f"Invalid disclosed index: {idx}")
        
        U = L - R  # Number of undisclosed messages
        
        # Sort disclosed indexes for consistency
        disclosed_indexes_sorted = sorted(disclosed_indexes)
        
        # Determine undisclosed indexes
        undisclosed_indexes = sorted([i for i in range(L) if i not in disclosed_indexes_sorted])
        
        # Split messages
        disclosed_messages = [messages[i] for i in disclosed_indexes_sorted]
        undisclosed_messages = [messages[i] for i in undisclosed_indexes]
        
        # Core.tex Step 1: Generate random scalars (5 + U scalars needed)
        random_scalars = self.calculate_random_scalars(5 + U)
        
        # Core.tex Step 2: Initialize proof
        init_res = self.proof_init(
            PK, signature, random_scalars,
            header, messages, undisclosed_indexes
        )
        
        # Core.tex Step 3: Calculate challenge
        challenge = self.proof_challenge_calculate(
            init_res, disclosed_messages,
            disclosed_indexes_sorted, ph
        )
        
        # Core.tex Step 4: Finalize proof
        proof = self.proof_finalize(
            init_res, challenge, signature.e,
            random_scalars, undisclosed_messages
        )
        
        return proof
    
    def core_proof_verify(self,
                         PK: BBSPublicKey,
                         proof: BBSProof,
                         header: bytes,
                         ph: bytes,
                         disclosed_messages: List[bytes],
                         disclosed_indexes: List[int]) -> bool:
        """
        CoreProofVerify operation from Core.tex Section 3.6.4
        
        Procedure :
        1. Initialize verification using ProofVerifyInit
        2. Recalculate challenge using ProofChallengeCalculate
        3. Verify challenge matches
        4. Verify pairing equation: h(Abar, W) * h(Bbar, -BP2) == Identity_GT
        """
        # Core.tex Step 1: Initialize verification
        init_res = self.proof_verify_init(
            PK, proof, header,
            disclosed_messages, disclosed_indexes
        )
        
        # Core.tex Step 2: Recalculate challenge
        challenge = self.proof_challenge_calculate(
            init_res, disclosed_messages,
            disclosed_indexes, ph
        )
        
        # Core.tex Step 3: Verify challenge matches
        if proof.cp != challenge:
            return False
        
        # Core.tex Step 4: Verify pairing equation
        pairing_1 = pairing(PK.W, proof.Abar)
        neg_P2 = neg(self.P2)
        pairing_2 = pairing(neg_P2, proof.Bbar)
        product = pairing_1 * pairing_2
        final = final_exponentiate(product)
        
        return final == FQ12.one()

class BBSWithProofs:
    """
    Complete BBS implementation with zero-knowledge proofs
    Combines CoreSign/CoreVerify with CoreProofGen/CoreProofVerify
    """
    
    def __init__(self, max_messages: int = 10, api_id: bytes = b""):
        self.max_messages = max_messages
        self.api_id = api_id
        
        # Create generators
        self.generators = BBSGenerators.create_generators(self.max_messages, self.api_id)
        
        # Initialize subsystems
        from BBSCore.bbsSign import BBSSignatureScheme
        
        self.sign_scheme = BBSSignatureScheme(
            max_messages=self.max_messages,
            api_id=self.api_id,
            generators=self.generators
        )
        
        self.proof_scheme = BBSProofScheme(
            max_messages=self.max_messages,
            api_id=self.api_id,
            generators=self.generators
        )
    
    def sign(self, sk: BBSPrivateKey, messages: List[bytes], 
            header: bytes = b"") -> BBSSignature:
        """Sign messages using CoreSign"""
        return self.sign_scheme.core_sign(sk, header, messages)
    
    def verify(self, pk: BBSPublicKey, signature: BBSSignature,
              messages: List[bytes], header: bytes = b"") -> bool:
        """Verify signature using CoreVerify"""
        return self.sign_scheme.core_verify(pk, signature, header, messages)
    
    def generate_proof(self, pk: BBSPublicKey, signature: BBSSignature,
                      header: bytes = b"", messages: Optional[List[bytes]] = None,
                      disclosed_indexes: Optional[List[int]] = None,
                      presentation_header: bytes = b"") -> BBSProof:
        """Generate zero-knowledge proof using CoreProofGen"""
        return self.proof_scheme.core_proof_gen(
            pk, signature, header, presentation_header,
            messages, disclosed_indexes
        )
    
    def verify_proof(self, pk: BBSPublicKey, proof: BBSProof,
                    header: bytes = b"", disclosed_messages: Optional[List[bytes]] = None,
                    disclosed_indexes: Optional[List[int]] = None,
                    presentation_header: bytes = b"") -> bool:
        """Verify zero-knowledge proof using CoreProofVerify"""
        return self.proof_scheme.core_proof_verify(
            pk, proof, header, presentation_header,
            disclosed_messages, disclosed_indexes
        )