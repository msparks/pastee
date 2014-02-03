package pastee

import (
	"errors"
	"fmt"
	"strconv"
	"strings"
)

// MBase31 is an integer -> string mapping that optimizes for readability and
// length. The character set does not contain ambiguous characters (i, l, o, 0,
// 1), and is all lowercase.
type MBase31 struct {
	Value int64
}

// "Regular" base31 character set:  0123456789abcdefghijklmnopqrstu
// "Modified" base31 character set: abcdefghjkmnpqrstuvwxyz23456789

// Encodes an integer value into an MBase31 string.
func (m MBase31) ToString() string {
	base31ToMBase31Mapping := map[rune]rune{
		'0': 'a', '1': 'b', '2': 'c', '3': 'd', '4': 'e', '5': 'f',
		'6': 'g', '7': 'h', '8': 'j', '9': 'k', 'a': 'm', 'b': 'n',
		'c': 'p', 'd': 'q', 'e': 'r', 'f': 's', 'g': 't', 'h': 'u',
		'i': 'v', 'j': 'w', 'k': 'x', 'l': 'y', 'm': 'z', 'n': '2',
		'o': '3', 'p': '4', 'q': '5', 'r': '6', 's': '7', 't': '8',
		'u': '9', '-': '-'}
	base31toMBase31 := func(r rune) rune {
		return base31ToMBase31Mapping[r]
	}

	return strings.Map(base31toMBase31, strconv.FormatInt(m.Value, 31))
}

// Decodes a MBase31-encoded string.
func MBase31FromString(mb31 string) (MBase31, error) {
	mBase31ToBase31Mapping := map[rune]rune{
		'a': '0', 'b': '1', 'c': '2', 'd': '3', 'e': '4', 'f': '5',
		'g': '6', 'h': '7', 'j': '8', 'k': '9', 'm': 'a', 'n': 'b',
		'p': 'c', 'q': 'd', 'r': 'e', 's': 'f', 't': 'g', 'u': 'h',
		'v': 'i', 'w': 'j', 'x': 'k', 'y': 'l', 'z': 'm', '2': 'n',
		'3': 'o', '4': 'p', '5': 'q', '6': 'r', '7': 's', '8': 't',
		'9': 'u', '-': '-'}

	// Verify input argument.
	for _, r := range mb31 {
		_, ok := mBase31ToBase31Mapping[r]
		if !ok {
			return MBase31{}, errors.New(
				fmt.Sprintf("rune '%s' is not in the MBase31 character set", string(r)))
		}
	}

	mBase31toBase31 := func(r rune) rune {
		return mBase31ToBase31Mapping[r]
	}

	value, err := strconv.ParseInt(strings.Map(mBase31toBase31, mb31), 31, 64)
	if err != nil {
		return MBase31{}, err
	}
	return MBase31{value}, nil
}
