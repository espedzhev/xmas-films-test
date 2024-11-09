import csv
import time

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

import shortuuid

from core.models import AccessCode

BATCH_SIZE = 10000
CHUNK_SIZE = 10000

ALPHABET = "0123456789" + "BCDFGHJKLMNPQRSTVWXYZ"
shortuuid.set_alphabet(ALPHABET)


def generate_formatted_code() -> str:
    code = shortuuid.random(length=16)
    return f"{code[:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"


def generate_shortuuid_batch(num_codes: int, existing_codes: set) -> set:
    codes = set()

    while len(codes) < num_codes:
        code = generate_formatted_code()

        if code not in existing_codes:
            codes.add(code)

    return codes


class Command(BaseCommand):
    help = "Generate random access codes in bulk and store them in the database and a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("num_codes", type=int, help="The number of access codes to generate.")

    def handle(self, *args, **options):
        start_time = time.time()
        num_codes_target = options["num_codes"]

        if num_codes_target <= 0:
            self.stdout.write(self.style.ERROR("Input was 0 - nothing to generate"))
            return

        num_codes_to_generate_counter = num_codes_target
        unique_codes = set()

        with open("access_codes.csv", "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)

            while num_codes_to_generate_counter > 0:
                batch_size = min(BATCH_SIZE, num_codes_to_generate_counter)
                success = False

                while not success:
                    # generate codes
                    codes_batch = set(generate_shortuuid_batch(batch_size, unique_codes))

                    # try inserting into db, if error occurs regenerate the batch
                    try:
                        codes_to_create = [AccessCode(value=code) for code in codes_batch]

                        with transaction.atomic():
                            AccessCode.objects.bulk_create(codes_to_create, batch_size=CHUNK_SIZE)

                        # write the generated codes into a file if successful
                        for code in codes_batch:
                            csv_writer.writerow([code])

                        # update counter and unique codes
                        num_codes_to_generate_counter -= len(codes_batch)
                        unique_codes.update(codes_batch)

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Generated and saved num of codes: {len(unique_codes):_}"
                            )
                        )

                        success = True
                    except IntegrityError:
                        self.stdout.write(
                            self.style.WARNING("IntegrityError occured, regenerating batch...")
                        )

        self.stdout.write(
            self.style.SUCCESS(f"Total execution time: {time.time() - start_time:.2f} seconds")
        )
