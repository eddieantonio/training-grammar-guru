#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2017 Eddie Antonio Santos <easantos@ualberta.ca>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Do evaluation.

Requirements:

 5. Evaluate location of change => MRR
 6. Can it fix this change?
 7. If it is an open-class, consider it UNFIXABLE!

This evaluation:
 - not representative of actual errors
 - demonstrates theoretical efficacy
 - intended to test algorithm given a number of different scenarios
"""

import argparse
import sys
import tempfile
import random

from vocabulary import vocabulary, START_TOKEN, END_TOKEN
from model_recipe import ModelRecipe
from token_utils import Token
from condensed_corpus import CondensedCorpus

# According to Campbell et al. 2014
MAX_MUTATIONS = 120

parser = argparse.ArgumentParser()
parser.add_argument('corpus', type=CondensedCorpus.connect_to)
parser.add_argument('model', type=ModelRecipe.from_string)
parser.add_argument('-k', '--mutations', type=int, default=MAX_MUTATIONS)


def random_token_from_vocabulary():
    """
    Gets a uniformly random token from the vocabulary as a vocabulary index.
    """
    # Generate anything EXCEPT the start and the end token.
    return random.randint(1, len(vocabulary))


class Model:
    ...


class Mutation:
    """
    Base class for all mutations, just for the sake of having a base class,
    really.
    """


class Addition(Mutation):
    __slots__ = ('insertion_point', 'token')

    def __init__(self, insertion_point, token):
        self.insertion_point = insertion_point
        self.token = token

    def format(self, program, file=sys.stdout):
        """
        Applies the mutation to the source code and writes it to a file.
        """
        insertion_point = self.insertion_point
        for index, token in enumerate(program):
            if index == insertion_point:
                file.write(vocabulary.to_text(self.token))
                file.write(' ')
            file.write(vocabulary.to_text(token))
            file.write(' ')
        file.write('\n')

    @classmethod
    def create_random_mutation(cls, program,
                               random_token=random_token_from_vocabulary):
        """
        Campbell et al. 2014:

            A location in the source file was chosen at random and a random
            token found in the same file was inserted there.

        random_token() is a function that returns a random token AS A
        VOCABULARY INDEX!
        """

        insertion_point = program.random_insertion_point()
        token = random_token()
        return cls(insertion_point, token)


class Deletion(Mutation):
    __slots__ = ('index')

    def __init__(self, index):
        self.index = index

    def format(self, program, file=sys.stdout):
        """
        Applies the mutation to the source code and writes it to a file.
        """
        delete_index = self.index
        for index, token in enumerate(program):
            if index == delete_index:
                continue
            file.write(vocabulary.to_text(token))
            file.write(' ')
        file.write('\n')

    @classmethod
    def create_random_mutation(cls, program):
        """
        Campbell et al. 2014:

            A token (lexeme) was chosen at random from the input source file
            and deleted. The file was then run through the querying and
            ranking process to determine where the first result with adjacent
            code appeared in the suggestions.
        """
        victim_index = program.random_index()
        return cls(victim_index)


class Substitution(Mutation):
    __slots__ = ('index', 'token')
    def __init__(self, index, token):
        self.index = index
        self.token = token

    def format(self, program, file=sys.stdout):
        """
        Applies the mutation to the source code and writes it to a file.
        """
        sub_index = self.index
        for index, token in enumerate(program):
            if index == sub_index:
                token = self.token
            file.write(vocabulary.to_text(token))
            file.write(' ')
        file.write('\n')

    @classmethod
    def create_random_mutation(cls, program,
                               random_token=random_token_from_vocabulary):
        """
        Campbell et al. 2014:

            A token was chosen at random and replaced with a random token
            found in the same file.

        random_token() is a function that returns a random token AS A
        VOCABULARY INDEX!
        """
        victim_index = program.random_index()
        token = random_token()
        return cls(victim_index, token)


class SourceCode(Mutation):
    """
    A source code file.
    """
    def __init__(self, file_hash, tokens):
        self.hash = file_hash
        self.tokens = tokens
        self.first_index = 1 if tokens[0] == vocabulary.start_token_index else 0
        last_index = len(tokens) - 1
        self.last_index = (
            last_index - 1 if tokens[-1] == vocabulary.end_token_index else last_index
        )

    def __iter__(self):
        return iter(self.tokens)

    def __len__(self):
        return len(self.tokens)

    def random_insertion_point(self, randint=random.randint):
        """
        Produces a random insertion point in the program. Does not include start and end
        tokens.
        """
        assert self.tokens[-1] == vocabulary.end_token_index
        return randint(self.first_index, self.last_index + 1)

    def random_index(self, randint=random.randint):
        """
        Produces a random insertion point in the program. Does not include start and end
        tokens.
        """
        return randint(self.first_index, self.last_index)


def test():
    program = SourceCode('DEADBEEF', [0, 86, 5, 31, 99])
    mutation = Addition.create_random_mutation(program)
    mutation.format(program)


def main():
    # Requires: corpus, model data (backwards and forwards)
    model = ...
    persist = ...
    for file_hash, tokens in corpus.files_in_fold(fold_no):
        program = SourceCode(file_hash, tokens)
        for mutation_kind in Addition, Deletion, Substitution:
            n_incorrect_files = 0
            while n_incorrect_files < MAX_MUTATIONS:
                mutation = mutation_kind.create_random_mutation(program)
                with tempfile.NamedTemporaryFile(encoding='UTF-8') as mutated_file:
                    # Apply the mutatation and flush it to disk.
                    mutation.format(mutation, mutated_file)
                    mutated_file.flush()

                    # TODO: Try the file, reject if it compiles.
                    if model.is_okay(tempfile.name):
                        persist.created_correct_file += 1
                        continue

                    # TODO: save as CSV.
                    # TODO: Count rank of correct token location
                    # TODO: Count how many times the suggestion compiles
                    # TODO: In paper, discuss how the file can still be
                    # correct, even with a different operation (give example).
                    # TODO: Count how many times the suggestion IS the true
                    # result.

                    results = model.detect(tempfile.name)
                    persist(program, mutation, results)
                    n_incorrect_files += 1

if __name__ == '__main__':
    test()
