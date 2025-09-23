package com.tariff.tariff_backend.repository;

import com.tariff.tariff_backend.model.tariffs_new.TariffNew;
import com.tariff.tariff_backend.model.tariffs_new.Country;
import org.springframework.data.jpa.repository.JpaRepository;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

public interface TariffNewRepo extends JpaRepository<TariffNew, Integer> {

    Optional<TariffNew> findByTariffId(Integer tariffId);

    List<TariffNew> findByDescriptionwcountry(String descriptionwcountry);

    List<TariffNew> findByPartnerCountry(Country partnerCountry);

    List<TariffNew> findByReporterCountry(Country reporterCountry);

    List<TariffNew> findByUnitname(String unitname);

    List<TariffNew> findByCategory(String category);

    List<TariffNew> findByAdValorem(BigDecimal adValorem);

    List<TariffNew> findBySpecificPerUnit(BigDecimal specificPerUnit);

    // Partial search
    List<TariffNew> findByDescriptionwcountryContainingIgnoreCase(String keyword);
}
