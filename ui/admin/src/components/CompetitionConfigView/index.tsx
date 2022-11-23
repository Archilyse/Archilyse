import { TreeItem, TreeView } from '@material-ui/lab';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import { Box, Button, Container, Grid, Typography } from '@material-ui/core';
import React, { useRef, useState } from 'react';
import { FeatureConfigInputs } from 'Components/CompetitionConfigView/FeatureConfigInputs';

function flatten(obj, prefix = null, current = null) {
  prefix = prefix || [];
  current = current || {};
  if (typeof obj === 'object' && obj !== null) {
    Object.keys(obj).forEach(key => {
      flatten(obj[key], prefix.concat(key), current);
    });
  } else {
    current[prefix.join('.')] = obj;
  }
  return current;
}

const FeaturesTreeView = props => {
  const showFeature = feature => {
    return props.showFeatures.includes(feature.code);
  };
  const showSection = section => {
    return section.sub_sections.some(feature => showFeature(feature));
  };
  const showCategory = category => {
    return category.sub_sections.some(section => showSection(section));
  };
  const onNodeSelect = (e, nodeId) => {
    if (props.showFeatures.includes(nodeId)) {
      props.onFeatureSelected(nodeId);
    }
  };

  return (
    <TreeView
      style={{ color: 'rgba(0, 0, 0, 0.54)' }}
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
      selected={props.selectedFeature}
      onNodeSelect={onNodeSelect}
      onNodeToggle={props.onNodeToggle}
    >
      {props.categories.filter(showCategory).map(category => {
        return (
          <TreeItem key={category.key} nodeId={category.key} label={category.name_en}>
            {category.sub_sections.filter(showSection).map(section => {
              return (
                <TreeItem key={section.key} nodeId={section.key} label={section.name_en}>
                  {section.sub_sections.filter(showFeature).map(feature => {
                    return <TreeItem key={feature.key} nodeId={feature.code} label={feature.name_en} />;
                  })}
                </TreeItem>
              );
            })}
          </TreeItem>
        );
      })}
    </TreeView>
  );
};

const FeatureConfigForm = props => {
  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <Typography component="h6" variant="h6">
          Configuration Data
        </Typography>
      </Grid>
      <Grid item xs={12}>
        <Grid container spacing={2}>
          <FeatureConfigInputs feature={props.feature} featureProps={props.featureProps} onChange={props.onChange} />
        </Grid>
        <Grid container justify="flex-start">
          <Grid item>
            <Box pt={6}>
              <Button type="submit" variant="contained" color="primary">
                Save Changes
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
};

const FeatureDescription = props => {
  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <Typography component="h4" variant="h5">
          {props.name}
        </Typography>
      </Grid>
      <Grid item xs={12}>
        <Typography component="h1" variant="subtitle2">
          {props.description}
        </Typography>
      </Grid>
    </Grid>
  );
};

const FeatureDetailView = props => {
  return (
    <>
      <Box pt={3} mb={3}>
        <FeatureDescription name={props.name} description={props.description} />
      </Box>
      <Box>
        <FeatureConfigForm
          formRef={props.formRef}
          onSubmit={props.onSubmit}
          feature={props.feature}
          featureProps={props.featureProps}
          onChange={props.onChange}
        />
      </Box>
    </>
  );
};

const featureKeyToConfigKeyMap = {
  RESIDENTIAL_USE_RATIO: ['residential_ratio'],
  RESIDENTIAL_USE: ['commercial_use_desired'],
  APT_RATIO_BEDROOM_MIN_REQUIREMENT: ['min_room_sizes'],
  APT_RATIO_BATHROOM_MIN_REQUIREMENT: ['min_bathroom_sizes'],
  JANITOR_OFFICE_MIN_SIZE_REQUIREMENT: ['janitor_office_min_size'],
  JANITOR_STORAGE_MIN_SIZE_REQUIREMENT: ['janitor_storage_min_size'],
  APT_PCT_W_STORAGE: ['min_reduit_size'],
  BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE: ['bikes_boxes_count_min'],
  APT_RATIO_NAVIGABLE_AREAS: ['min_corridor_size'],
  APT_MIN_OUTDOOR_REQUIREMENT: ['min_outdoor_area_per_apt'],
  RESIDENTIAL_TOTAL_HNF_REQ: ['total_hnf_req'],
  APT_SIZE_DINING_TABLE_REQ: ['dining_area_table_min_big_side', 'dining_area_table_min_small_side'],
};

const CompetitionConfigView = props => {
  const [selectedFeature, setSelectedFeature] = useState('');
  const [competition, setCompetition] = useState(props.competition);
  const formRef = useRef(null);

  const features = {};
  props.categories.forEach(c =>
    c.sub_sections.forEach(s =>
      s.sub_sections.forEach(f => {
        features[f.code] = { name: f.name_en, description: f.info_en };
      })
    )
  );

  const showFeatures = Object.keys(featureKeyToConfigKeyMap).filter(
    k => !competition.features_selected || competition.features_selected.includes(k)
  );

  const onChange = (name, value) => {
    const path = name.split('.');
    const property = path.pop();
    let pointer = competition.configuration_parameters;
    path.forEach(el => {
      pointer[el] = { ...pointer[el] };
      pointer = pointer[el];
    });
    pointer[property] = value;
    setCompetition({ ...competition });
  };

  const onSubmit = async e => {
    e.preventDefault();
    if (e.target.checkValidity()) {
      await props.onSubmit(competition);
    }
  };

  const onFeatureSelected = feature => {
    if (formRef.current.checkValidity()) {
      setSelectedFeature(feature);
    } else {
      formRef.current.reportValidity();
    }
  };

  const getFeatureProps = feature => {
    const featureConfigValues = {};
    const fields = featureKeyToConfigKeyMap[feature];
    if (fields) {
      fields.forEach(field => {
        featureConfigValues[field] = competition.configuration_parameters[field];
      });
      return flatten(featureConfigValues);
    }
  };

  return (
    <Container maxWidth="md">
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <h2 style={{ textAlign: 'center' }}>{props.competition.name}</h2>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Box pt={3} pr={0}>
            <FeaturesTreeView
              selectedFeature={selectedFeature}
              categories={props.categories}
              showFeatures={showFeatures}
              onFeatureSelected={onFeatureSelected}
            />
          </Box>
        </Grid>
        <Grid item xs={12} sm={8}>
          <form ref={formRef} onSubmit={onSubmit}>
            {selectedFeature ? (
              <FeatureDetailView
                feature={selectedFeature}
                featureProps={getFeatureProps(selectedFeature)}
                name={features[selectedFeature].name}
                description={features[selectedFeature].description}
                onChange={onChange}
                onSubmit={onSubmit}
              />
            ) : null}
          </form>
        </Grid>
      </Grid>
    </Container>
  );
};

export default CompetitionConfigView;
