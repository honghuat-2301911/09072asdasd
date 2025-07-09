// Implementation of the Paillier Cryptosystem in Go.
// The Paillier Cryptosystem was invented by Pascal Paillier in 1999, and
// is a probabilistic asymmetric algorithm for public key cryptography.
// It has homomorphic properties and is non-deterministic.
// It supports addition and multiplication of plaintext to ciphertexts.

package paillier

import (
	"crypto/rand"
	"errors"
	"math/big"
)

type ITYPES interface {
	PublicKey | PrivateKey

	IsEqual(other interface{}) bool
}

// =============================================================================
// Operations
// =============================================================================

// Generates a pair of public and private keys for encryption, decryption & arithmetic operations.
// This follows the key generation algorithm, which can be found here:
// https://en.wikipedia.org/wiki/Paillier_cryptosystem
func GenerateKeys(length int) (*PublicKey, *PrivateKey, error) {

	if length < 16 {
		return nil, nil, errors.New("length must be greater than 16")
	}

	var err error

	// Generate prime numbers p & q based on given length
	p, err := rand.Prime(rand.Reader, length)
	if err != nil {
		return nil, nil, err
	}
	q, err := rand.Prime(rand.Reader, length)
	if err != nil {
		return nil, nil, err
	}

	one := new(big.Int).SetInt64(1)

	// Compute public key variables
	// n = p * q
	// n^2 = n * n (we compute this for faster encryption & decryption)
	// g = n + 1 (simpler variation instead of all integers between 1 & n^2 due to size)
	var (
		n        = new(big.Int).Mul(p, q)
		nSquared = new(big.Int).Mul(n, n)
		g        = new(big.Int).Add(n, one)
	)

	// Compute private key variables
	// lambda = (p - 1)(q - 1)
	// mu = lambda^-1 % n
	var (
		pMinus1 = new(big.Int).Sub(p, one)
		qMinus1 = new(big.Int).Sub(q, one)
		lambda  = new(big.Int).Mul(pMinus1, qMinus1)
		mu      = new(big.Int).ModInverse(lambda, n)
	)

	var (
		newPublicKey  = &PublicKey{n, nSquared, g, int64(length)}
		newPrivateKey = &PrivateKey{lambda, mu, int64(length)}
	)

	return newPublicKey, newPrivateKey, nil
}

// Encrypts a given value using the public key.
// Returns an error if rng fails or if value does not satisfy 0 <= value < N
func Encrypt(publicKey *PublicKey, value *big.Int) (*big.Int, error) {
	if value.Cmp(publicKey.N) != -1 {
		return nil, errors.New("value is too large to encrypt")
	}

	one := new(big.Int).SetInt64(1)
	length := new(big.Int).SetInt64(publicKey.Length)

	// Select random number such that 0 < r < n and gcd(r,n) = 1
	// We keep trying until we get a valid number
	// This step can be expensive due to this infinite loop
	// TODO: Add timeout?
	var err error
	var r *big.Int

	for {
		if r, err = rand.Int(rand.Reader, length); err != nil {
			return nil, err
		}

		if gdc := new(big.Int).GCD(nil, nil, r, publicKey.N); gdc.Cmp(one) == 0 {
			break
		}
	}

	// Compute ciphertext
	// c = (g^m * r^n) % n^2
	var (
		gM = new(big.Int).Exp(publicKey.G, value, publicKey.NSquare)
		rN = new(big.Int).Exp(r, publicKey.N, publicKey.NSquare)
		c  = new(big.Int).Mod(new(big.Int).Mul(gM, rN), publicKey.NSquare)
	)

	return c, nil
}

// Encrypts a given value using a matching set of public & private keys.
// Returns an error value if value >= n^2
func Decrypt(publicKey *PublicKey, privateKey *PrivateKey, value *big.Int) (*big.Int, error) {
	if value.Cmp(publicKey.NSquare) != -1 {
		return nil, errors.New("value is too large to decrypt")
	}

	// Compute variables to decrypt
	// L(x) = (x - 1)/n
	// m 	= L * mu % n
	//   	= (((c^Lambda % n^2) - 1) / n) * mu % n

	one := new(big.Int).SetInt64(1)

	var (
		x = new(big.Int).Exp(value, privateKey.Lambda, publicKey.NSquare)
		l = new(big.Int).Div(new(big.Int).Sub(x, one), publicKey.N)
		m = new(big.Int).Mod(new(big.Int).Mul(l, privateKey.Mu), publicKey.N)
	)

	return m, nil
}

// =============================================================================
// Homomorphic Operations
// =============================================================================

func AddEncryptedWithPlain(publicKey *PublicKey, encrypted, plain *big.Int) *big.Int {
	// m1 + m2 = m1 * g^m2 % n^2
	gPowerM2 := new(big.Int).Exp(publicKey.G, plain, nil)
	return new(big.Int).Mod(new(big.Int).Mul(encrypted, gPowerM2), publicKey.NSquare)
}

func AddEncrypted(publicKey *PublicKey, lhs, rhs *big.Int) *big.Int {
	// m1 + m2 = m1 * m2 % n^2
	return new(big.Int).Mod(new(big.Int).Mul(lhs, rhs), publicKey.NSquare)
}

// =============================================================================
// Public Key
// =============================================================================

type PublicKey struct {
	N       *big.Int `json:"N"`
	NSquare *big.Int `json:"NSquare"`
	G       *big.Int `json:"G"`
	Length  int64    `json:"Length"`
}

func (k PublicKey) IsEqual(other interface{}) bool {
	otherObj, ok := other.(PublicKey)
	if !ok {
		return false
	}

	if k.N.Cmp(otherObj.N) != 0 {
		return false
	}

	if k.NSquare.Cmp(otherObj.NSquare) != 0 {
		return false
	}

	if k.G.Cmp(otherObj.G) != 0 {
		return false
	}

	if k.Length != otherObj.Length {
		return false
	}

	return true
}

// =============================================================================
// Private Key
// =============================================================================

type PrivateKey struct {
	Lambda *big.Int `json:"Lambda"`
	Mu     *big.Int `json:"Mu"`
	Length int64    `json:"Length"`
}

func (k PrivateKey) IsEqual(other interface{}) bool {
	otherObj, ok := other.(PrivateKey)
	if !ok {
		return false
	}

	if k.Lambda.Cmp(otherObj.Lambda) != 0 {
		return false
	}

	if k.Mu.Cmp(otherObj.Mu) != 0 {
		return false
	}

	if k.Length != otherObj.Length {
		return false
	}

	return true
}
