# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

## Purpose

This repository provides a research-focused and educational implementation of the BBS (Boneh–Boyen–Shacham) signature scheme in Python, applied to the use case of Digital Travel Credentials (DTC). The implementation uses BLS12-381 elliptic curve cryptography with SHA-256 hashing and is designed for educational and research purposes in the context of digital identity and selective disclosure.

It demonstrates:
- Selective disclosure via BBS zero-knowledge proofs
- Privacy-preserving issuance using blind signatures
- A full credential lifecycle: issuance, storage, presentation, and verification

The target audience includes students learning cryptography and contributors exploring privacy-preserving identity systems.

- A complete plan for the project has been written to plan.md


---

## Key Architecture Components

### Core Cryptographic Layer (`BBSCore/`)
- **Setup.py**: Initializes parameters, key structures, and generator precomputation
- **bbsSign.py**: Main BBS signature scheme implementation with sign, verify, proof generation/verification
- **BlindSign.py**: Blind signature protocols for privacy-preserving issuance
- **KeyGen.py**: Key generation utilities for BBS keys
- **ZKProof.py**: Zero-knowledge proof generation and verification
- **security_utils.py**: Security-related utilities and helpers

### Digital Trust Certificate Layer (`DTC/`)
- **dtc.py**: Core DTC data structures and credential definitions
- **DTCIssuer.py**: Credential issuance functionality
- **DTCHolder.py**: Credential storage and presentation logic
- **DTCVerifier.py**: Credential verification and validation
- **bbs_core.py**: Integration layer between DTC and BBS core

### Performance & Benchmarking (`benchmark/`)
- **runner.py**: Main benchmark execution and CLI interface
- **collector.py**: Metrics collection for performance measurement
- **config.py**: Benchmark configuration and parameters
- **scenarios.py**: Integration with Demo scenarios to avoid code duplication
- **visualization/**: Graph generation and performance visualization
- **data/**: JSON data management for personalized benchmarks

### Demonstration Layer (`Demo/`)
- **basic_bbs.py**: Basic BBS signature demonstrations
- **demo_travel.py**: Complete travel credential workflow
- **credential_issuance.py**: Credential issuance demonstrations

### External Dependencies (`Externe/`)
- Cryptographic primitives adapted from Chia Network and Algorand
- **ec.py**, **fields.py**, **pairing.py**: Elliptic curve operations
- **opt_swu_g1.py**, **opt_swu_g2.py**: Optimized SWU mapping implementations
- **bls12381.py**: BLS12-381 curve implementation

### Configuration Layer
- **config.py** (root): Global project configuration integrating benchmark settings
- **benchmark/config.py**: Dedicated benchmark configuration
- BLS12-381 curve constants, domain separation tags (DSTs)
- Ciphersuite configuration (based on IETF BBS draft)
- Hash function selection (SHA-256 or SHAKE256)

---

## External Dependencies & Cryptographic Sources
The implementation leverages external cryptographic components:

- **Hashing**: `pycryptodome` for SHAKE-256 support
- **Encoding**: `base58` for compact, human-readable serialization
- **Elliptic Curve Utilities**: Code adapted from Chia Network:
  - `ec.py`, `fields.py`, `pairing.py`, `key.py`, `hashes.py`
- **Mapping to Curve**: SWU implementation from Algorand for G1/G2 mapping:
  - `opt_swu_g1.py`, `opt_swu_g2.py`

All cryptographic code follows best practices in terms of domain separation and parameter configuration, but **should not be used in production without review**.

---

## Credential Lifecycle

[ Issuer ] → Issue VC → [ Holder ] → Present Proof → [ Verifier ]
1. **Issuer** signs a Verifiable Credential (VC) using BBS signatures
2. **Holder** generates a zero-knowledge proof for selected attributes
3. **Verifier** validates the proof and disclosed data using the issuer's public key

Each actor has a corresponding module and API endpoint.

---


## Core BBS Signature Flow

1. **Setup**
    - Initialize global system parameters, including the maximum number of messages (`L`) supported by the ciphersuite.
    - Generate required generators on the BLS12-381 curve for both G1 and G2 groups.
    - Define domain separation tags (DSTs) according to the IETF draft to avoid cross-protocol attacks.

2. **Key Generation**
    - Randomly sample a secret key `sk` from the scalar field of BLS12-381.
    - Derive the public key `pk` as `pk = sk * G2_generator`.

3. **Signing**
    - Serialize each message into canonical form, UTF-8 encoded.
    - Map each message to a point in G1 via the SWU (Shallue–van de Woestijne–Ulas) mapping.
    - Compute the signature `(A, e)` using the secret key, message points, and precomputed generators.

4. **Verification**
    - Recompute the message points from the received messages.
    - Perform pairing-based checks to verify that `(A, e)` is a valid signature under `pk` for the given set of messages.

5. **Proof Generation (Selective Disclosure)**
    - Given a valid signature and all original messages, choose an index set `R` of attributes to reveal.
    - Randomize the signature `(A, e)` with fresh blinding factors.
    - Create a zero-knowledge proof that:
      - Proves the signature is valid for all attributes.
      - Binds the proof to a verifier-supplied nonce for replay protection.
      - Reveals only the attributes in `R`.

6. **Proof Verification**
    - Check the pairing equations on the randomized proof to confirm it could only be produced from a valid signature.
    - Verify the disclosed attributes match the proof commitments.
    - Ensure the nonce is correct and unused to guarantee freshness.

---

## Selective Disclosure: Detailed Explanation

BBS signatures allow a holder to prove possession of a credential without revealing all the signed attributes. The selective disclosure process works as follows:

- A holder possesses a credential signed over `n` attributes:  
  `[attr_0, attr_1, ..., attr_{n-1}]`

- The holder selects a subset `R ⊂ {0, …, n-1}` to reveal.

- For hidden attributes, commitments are created instead of plaintext values.

- The proof contains:
  - The disclosed values for all indices in `R`.
  - Commitments for indices not in `R`.
  - A randomized signature proof bound to a verifier-provided challenge/nonce.

Verifier’s guarantees:
- Can verify that disclosed values were indeed signed by the issuer.
- Learns nothing about hidden attributes beyond their existence.
- Cannot correlate multiple presentations from the same credential (unlinkability).
This is achieved through zero-knowledge proofs embedded into the BBS proof generation, ensuring security against adaptive disclosure attacks.

---

## Digital Trust Credential (DTC) Flow

1. **Issuer Setup**
    - A trusted authority (e.g., a government) generates a BBS key pair.
    - Defines a credential schema, e.g.:  
      `[name, date_of_birth, nationality, passport_number]`

2. **Credential Issuance**
    - The issuer serializes and signs the attributes using the BBS scheme.
    - Optionally, blind issuance is used so the issuer cannot see the final bound attributes.

3. **Holder Storage**
    - The holder securely stores the credential (full attributes + original signature) in a wallet or secure storage system.

4. **Selective Presentation**
    - For a verification request, the holder generates a selective disclosure proof revealing only the requested attributes.
    - This proof is non-interactive, unlinkable, and bound to a verifier’s nonce.

5. **Verification**
    - The verifier checks:
      - The revealed attributes match the commitments.
      - The proof is valid and derived from a legitimate BBS signature.
      - The signature matches the issuer’s public key.
      - The nonce has not been used before (replay prevention).

---


## Serialization Policy – Canonical JSON

- UTF-8, sorted keys, no extra whitespace.
- Strings in NFC, integers in canonical decimal, dates in ISO 8601.
- No pre-hashed messages allowed.

---

## Size Constraints & Benchmarks

- Max `L` = 128.
- Benchmark for `L` = 8, 16, 32, 64, 128 for all operations.
- CSV template:

```csv
L,Sign(ms),Verify(ms),ProofGen(ms),ProofVerify(ms),Memory(KB)
8,12.5,15.2,25.1,27.8,1024
```


## Running Tests
```bash
# Run all tests (currently commented out in main.py)
python main.py test

# Run specific test modules directly
python Test/test_basic.py      # Basic BBS operations
python Test/test_dtc.py        # DTC workflow tests
python Test/test_blind.py      # Blind signature tests
python Test/test_flow.py       # Integration tests
python Test/test_metrics.py    # Performance tests

# Alternative with pytest
python -m pytest Test/tests.py
python -m pytest Test/ -v     # Run all tests with verbose output
```

### Running Demos
```bash
# Complete travel scenario with selective disclosure
python main.py travel

# Basic BBS signature demonstration
python main.py demo

# Performance benchmarks with visualizations
python main.py benchmark

# Complete demonstration (tests + demos + benchmarks)
python main.py all

# Verbose mode with detailed performance metrics
python main.py <command> --verbose

# Disable optimizations for comparison
python main.py <command> --no-optimization
```

### Performance Optimization
```bash
# Generate all performance graphs
python generate_all_graphs.py

# M1-specific optimization guide
python m1_optimization_guide.py
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Quick verification
python Test/test_basic.py

# Development tools
python -m black .          # Code formatting
python -m pylint BBSCore/  # Linting (if available)
```

### Benchmark & Visualization Commands
```bash
# Run modular benchmark suite v2.0
python -c "from benchmark import BenchmarkRunner; BenchmarkRunner().run()"

# Generate performance visualizations
python benchmark/visualization/graphs.py       # Basic graphs
python benchmark/visualization/extra_graphs.py # Advanced graphs

# Work with personalized JSON data
python benchmark/data/data_personalized.py

# Export results in multiple formats
python benchmark/visualization/export.py
```

## Core BBS Signature Flow
1. **Setup**: Generate system parameters for maximum number of messages
2. **Key Generation**: Create BBS secret key (scalar) and public key (G2 point)
3. **Signing**: Create BBS signature on multiple messages
4. **Verification**: Verify signature against messages and public key
5. **Proof Generation**: Create zero-knowledge proof with selective disclosure
6. **Proof Verification**: Verify ZK proof reveals only intended attributes

## DTC Travel Credential Flow
1. **Issuer Setup**: Government/authority creates BBS keys
2. **Credential Issuance**: Sign travel document attributes (passport, visa, etc.)
3. **Holder Storage**: Traveler stores signed credentials
4. **Selective Presentation**: Traveler reveals only required attributes to verifier
5. **Verification**: Border control/airline validates presentation without seeing hidden attributes

## Important Cryptographic Notes
- Uses BLS12-381 pairing-friendly curve with 128-bit security
- Implements IETF BBS signature draft specifications
- SHA-256 for hashing (configurable to SHAKE-256)
- Supports blind signatures for privacy-preserving issuance
- All operations use proper domain separation tags for security

## Testing Strategy
The test suite validates:
- Basic BBS signature operations (`test_basic.py`)
- Blind signature protocols (`test_blind.py`) 
- Complete DTC workflow (`test_dtc.py`)
- Integration testing (`test_flow.py`)
- Performance benchmarks (`test_metrics.py`)


## Security Considerations
This is an educational implementation and should not be used in production without:
- Formal security audit
- Constant-time cryptographic operations
- Side-channel attack mitigations
- Proper randomness sources
- Key management infrastructure

## Specification References
- IETF BBS Signatures Draft: https://datatracker.ietf.org/doc/draft-irtf-cfrg-bbs-signatures/
- W3C Verifiable Credentials (v2): https://www.w3.org/TR/vc-data-model-2.0/

### Performance Optimization System
The codebase includes an integrated performance optimization system (`performance_optimizer.py`):
- Generator caching and pairing optimization
- Parallel processing for batch operations
- Memory pooling and monitoring
- Detailed performance reporting when using `--verbose` flag
- M1-specific optimizations available via `m1_optimization_guide.py`

All main.py commands support:
- `--verbose`: Detailed performance metrics and optimization reports
- `--no-optimization`: Disable optimizations for comparison benchmarks
- `--workers N`: Control parallel processing workers

### Critical Rules - DO NOT VIOLATE
- **NEVER create mock data or simplified components** unless explicitly told to do so
- **NEVER replace existing complex components with simplified versions** - always fix the actual problem
- **ALWAYS work with the existing codebase** - do not create new simplified alternatives
- **ALWAYS find and fix the root cause** of issues instead of creating workarounds
- When debugging issues, focus on fixing the existing implementation, not replacing it
- When something doesn't work, debug and fix it - don't start over with a simple version

### Working with the Modular Architecture
- The benchmark system (v2.0) is modular - avoid duplicating cryptographic code
- Use `benchmark/scenarios.py` to connect to existing Demo implementations
- Performance data is managed through JSON configurations in `benchmark/data/`
- All visualizations go through the centralized visualization engines