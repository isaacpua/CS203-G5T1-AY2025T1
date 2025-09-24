package com.tariff.tariff_backend.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.tariff.tariff_backend.model.tariffs_new.Country;

public interface CountryRepo extends JpaRepository<Country, Integer> {
    Optional<Country> findByCountryId(Integer countryId);

    Optional<Country> findByIso2(String iso2);

    List<Country> findByName(String name);

    List<Country> findAllByOrderByNameAsc();

    Optional<Country> findByIso2IgnoreCase(String iso2);

    List<Country> findByNameContainingIgnoreCaseOrderByNameAsc(String namePart);
}
